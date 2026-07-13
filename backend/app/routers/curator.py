from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..access import grant_read_access
from ..converters import to_artifact_read
from ..db import get_session
from ..models import Artifact, Request as RequestModel, Tag, User
from ..schemas import ArtifactRead, RequestDecision, RequestRead, RequestStatusUpdate, TagsUpdate
from ..security import require_role

router = APIRouter(prefix="/curator", tags=["curator"])


@router.get("/artifacts", response_model=List[ArtifactRead])
def list_artifacts_for_curator(
    status: Optional[str] = Query(
        default=None,
        description="Фильтр по curator_status: draft | approved | rejected",
    ),
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    query = select(Artifact)
    if status:
        query = query.where(Artifact.curator_status == status)
    artifacts = session.exec(query).all()
    return [to_artifact_read(a) for a in artifacts]


def _get_artifact_or_404(artifact_id: int, session: Session) -> Artifact:
    artifact = session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.post("/artifacts/{artifact_id}/approve", response_model=ArtifactRead)
def approve_artifact(
    artifact_id: int,
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    artifact = _get_artifact_or_404(artifact_id, session)
    artifact.curator_status = "approved"
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return to_artifact_read(artifact)


@router.post("/artifacts/{artifact_id}/reject", response_model=ArtifactRead)
def reject_artifact(
    artifact_id: int,
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    artifact = _get_artifact_or_404(artifact_id, session)
    artifact.curator_status = "rejected"
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return to_artifact_read(artifact)


@router.put("/artifacts/{artifact_id}/tags", response_model=ArtifactRead)
def update_artifact_tags(
    artifact_id: int,
    data: TagsUpdate,
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    artifact = _get_artifact_or_404(artifact_id, session)
    tags = session.exec(select(Tag).where(Tag.id.in_(data.tag_ids))).all()

    found_ids = {t.id for t in tags}
    missing = set(data.tag_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=400, detail=f"Unknown tag_ids: {sorted(missing)}"
        )

    artifact.tags = tags  # полная перезапись списка тегов, а не добавление
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return to_artifact_read(artifact)


@router.get("/requests", response_model=List[RequestRead])
def list_requests(
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    requests = session.exec(select(RequestModel)).all()
    return [RequestRead(**r.dict()) for r in requests]


@router.post("/requests/{request_id}/decision", response_model=RequestRead)
def decide_on_request(
    request_id: int,
    data: RequestDecision,
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    """Куратор/админ принимает или отклоняет запрос партнёра на полный текст.
    Если approve=True — выдаём доступ через PartnerArtifactAccess.
    """
    req = session.get(RequestModel, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.type != "full_text":
        raise HTTPException(
            status_code=400, detail="Only full_text requests can be decided by curator"
        )

    if req.status != "sent":
        raise HTTPException(
            status_code=400, detail=f"Request already in status '{req.status}'"
        )

    if data.approve:
        req.status = "approved"
        grant_read_access(session, req.artifact_id, req.partner_id)
    else:
        req.status = "rejected"

    session.add(req)
    session.commit()
    session.refresh(req)
    return RequestRead(**req.dict())


@router.patch("/requests/{request_id}/status", response_model=RequestRead)
def update_request_status(
    request_id: int,
    data: RequestStatusUpdate,
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    """Обновление статуса запроса (для запросов, уже обработанных)."""
    valid_statuses = {"in_progress", "done"}
    if data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of {sorted(valid_statuses)}",
        )

    req = session.get(RequestModel, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    req.status = data.status
    session.add(req)
    session.commit()
    session.refresh(req)
    return RequestRead(**req.dict())