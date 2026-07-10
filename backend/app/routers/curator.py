from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, requests
from sqlmodel import Session, select, func
from ..converters import to_artifact_read
from ..db import get_session
from ..models import Artifact, Request as RequestModel, Tag, User
from ..schemas import ArtifactRead, ArtifactShortRead, PartnerShortRead, RequestRead, RequestStatusUpdate, TagsUpdate
from ..security import require_role

router = APIRouter(prefix="/curator", tags=["curator"])


@router.get("/artifacts", response_model=List[ArtifactRead])
def list_artifacts_for_curator(
    status: Optional[str] = Query(
        default=None, description="Фильтр по curator_status: draft | approved | rejected"
    ),
    user: User = Depends(require_role("curator")),
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
    user: User = Depends(require_role("curator")),
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
    user: User = Depends(require_role("curator")),
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
    user: User = Depends(require_role("curator")),
    session: Session = Depends(get_session),
):
    artifact = _get_artifact_or_404(artifact_id, session)

    tags = session.exec(select(Tag).where(Tag.id.in_(data.tag_ids))).all()
    found_ids = {t.id for t in tags}
    missing = set(data.tag_ids) - found_ids
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown tag_ids: {sorted(missing)}")

    artifact.tags = tags  # полная перезапись списка тегов, а не добавление
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return to_artifact_read(artifact)

def to_request_read(req: RequestModel) -> RequestRead:
    return RequestRead(
        id=req.id,
        artifact=ArtifactShortRead(
            id=req.artifact.id,
            title=req.artifact.title,
        ),
        partner=PartnerShortRead(
            id=req.partner.id,
            name=req.partner.name,
        ),
        type=req.type,
        status=req.status,
        created_at=req.created_at,
    )

@router.get("/requests", response_model=List[RequestRead])
def list_requests(
    user: User = Depends(require_role("curator")),
    session: Session = Depends(get_session),
):
    requests = session.exec(select(RequestModel)).all()

    return [to_request_read(req) for req in requests]


@router.patch("/requests/{request_id}", response_model=RequestRead)
def update_request_status(
    request_id: int,
    data: RequestStatusUpdate,
    user: User = Depends(require_role("curator")),
    session: Session = Depends(get_session),
):
    req = session.get(RequestModel, request_id)

    if not req:
        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )

    req.status = data.status

    session.add(req)
    session.commit()
    session.refresh(req)

    return to_request_read(req)

@router.get("/artifacts/{artifact_id}", response_model=ArtifactRead)
def get_artifact(
    artifact_id: int,
    user: User = Depends(require_role("curator")),
    session: Session = Depends(get_session),
):
    artifact = _get_artifact_or_404(artifact_id, session)
    return to_artifact_read(artifact)


@router.get("/stats")
def curator_stats(
    user: User = Depends(require_role("curator")),
    session: Session = Depends(get_session),
):
    draft_count = session.exec(
        select(func.count())
        .select_from(Artifact)
        .where(Artifact.curator_status == "draft")).one()
    requests_count = session.exec(
        select(func.count())
        .select_from(RequestModel)
        .where(RequestModel.status == "sent")).one()
    return {"draft": draft_count, "requests": requests_count}