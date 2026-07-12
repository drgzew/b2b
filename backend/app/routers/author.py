from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..access import grant_read_access
from ..converters import to_artifact_read
from ..db import get_session
from ..models import Artifact, Author, Request as RequestModel, User
from ..schemas import (
    ArtifactRead,
    AuthorJobStatusUpdate,
    AuthorRead,
    AuthorRequestRead,
    ReadPolicyUpdate,
    RequestDecision,
    RequestRead,
)
from ..security import require_role

router = APIRouter(prefix="/author", tags=["author"])


def _get_own_author_or_400(user: User, session: Session) -> Author:
    if not user.author_id:
        raise HTTPException(status_code=400, detail="User is not linked to an author profile")
    author = session.get(Author, user.author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author profile not found")
    return author


@router.get("/me", response_model=AuthorRead)
def get_my_profile(
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    author = _get_own_author_or_400(user, session)
    return AuthorRead(**author.dict())


@router.patch("/me/job-status", response_model=AuthorRead)
def update_my_job_status(
    data: AuthorJobStatusUpdate,
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    """Самостоятельный выбор статуса в кабинете автора — в отличие от
    PATCH /authors/{id}/job-status в routers/authors.py, который тот же
    статус меняет от лица куратора/админа (например, со слов автора)."""
    valid_statuses = {"searching", "not_searching", "employed"}
    if data.job_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"job_status must be one of {sorted(valid_statuses)}",
        )

    author = _get_own_author_or_400(user, session)
    author.job_status = data.job_status
    session.add(author)
    session.commit()
    session.refresh(author)
    return AuthorRead(**author.dict())


@router.get("/artifacts", response_model=List[ArtifactRead])
def list_my_artifacts(
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    author = _get_own_author_or_400(user, session)
    return [to_artifact_read(a) for a in author.artifacts]


def _get_own_artifact_or_404(artifact_id: int, author: Author, session: Session) -> Artifact:
    artifact = session.get(Artifact, artifact_id)
    if not artifact or artifact.author_id != author.id:
        # 404, а не 403 — не подтверждаем сам факт существования чужого артефакта,
        # тот же принцип, что и у Subscription/Internship в routers/partner.py.
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.patch("/artifacts/{artifact_id}/read-policy", response_model=ArtifactRead)
def update_read_policy(
    artifact_id: int,
    data: ReadPolicyUpdate,
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    """Автор решает: открыть работу для чтения всем партнёрам сразу ('open')
    или требовать подтверждение на каждый запрос ('requires_approval', дефолт —
    'по умолчанию стоит запрет')."""
    valid = {"open", "requires_approval"}
    if data.read_policy not in valid:
        raise HTTPException(status_code=400, detail=f"read_policy must be one of {sorted(valid)}")

    author = _get_own_author_or_400(user, session)
    artifact = _get_own_artifact_or_404(artifact_id, author, session)

    artifact.read_policy = data.read_policy
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return to_artifact_read(artifact)


def _to_author_request_read(req: RequestModel) -> AuthorRequestRead:
    return AuthorRequestRead(
        id=req.id,
        artifact_id=req.artifact_id,
        artifact_title=req.artifact.title if req.artifact else "",
        partner_id=req.partner_id,
        partner_name=req.partner.name if req.partner else "",
        status=req.status,
        created_at=req.created_at,
    )


@router.get("/requests", response_model=List[AuthorRequestRead])
def list_my_requests(
    status: Optional[str] = Query(
        default=None, description="Фильтр по статусу: sent | approved | rejected"
    ),
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    """Запросы на полный текст по работам этого автора. Отображает компанию
    и название работы — не голые id (см. AuthorRequestRead)."""
    author = _get_own_author_or_400(user, session)

    query = select(RequestModel).where(RequestModel.type == "full_text")
    requests = session.exec(query).all()
    mine = [r for r in requests if r.artifact and r.artifact.author_id == author.id]
    if status:
        mine = [r for r in mine if r.status == status]
    return [_to_author_request_read(r) for r in mine]


@router.post("/requests/{request_id}/decision", response_model=RequestRead)
def decide_on_request(
    request_id: int,
    data: RequestDecision,
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    """Кнопка 'разрешить/нет' в кабинете автора. Одобрение выдаёт партнёру
    доступ именно к этому артефакту (см. app/access.py) — не открывает работу
    всем подряд и не меняет read_policy на будущее."""
    author = _get_own_author_or_400(user, session)

    req = session.get(RequestModel, request_id)
    if not req or req.type != "full_text" or not req.artifact or req.artifact.author_id != author.id:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status != "sent":
        raise HTTPException(status_code=400, detail=f"Request already decided: '{req.status}'")

    req.status = "approved" if data.approve else "rejected"
    req.decided_by = "author"
    req.decided_at = datetime.utcnow()
    session.add(req)
    session.commit()

    if data.approve:
        grant_read_access(session, artifact_id=req.artifact_id, partner_id=req.partner_id)

    session.refresh(req)
    return RequestRead(**req.dict())
