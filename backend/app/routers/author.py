from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..access import grant_read_access
from ..converters import to_artifact_read
from ..db import get_session
from ..models import Artifact, Author, Internship, Request as RequestModel, User
from ..schemas import (
    ArtifactRead,
    AuthorJobStatusUpdate,
    AuthorRead,
    AuthorRequestRead,
    ReadPolicyUpdate,
    RequestDecision,
    RequestRead,
    InternshipResponse,
)
from ..security import require_role

router = APIRouter(prefix="/author", tags=["author"])


def _get_own_author_or_400(user: User, session: Session) -> Author:
    if not user.author_id:
        raise HTTPException(
            status_code=400, detail="User is not linked to an author profile"
        )
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
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.patch("/artifacts/{artifact_id}/read-policy", response_model=ArtifactRead)
def update_read_policy(
    artifact_id: int,
    data: ReadPolicyUpdate,
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    valid = {"open", "requires_approval"}
    if data.read_policy not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"read_policy must be one of {sorted(valid)}",
        )
    author = _get_own_author_or_400(user, session)
    artifact = _get_own_artifact_or_404(artifact_id, author, session)
    artifact.read_policy = data.read_policy
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return to_artifact_read(artifact)


@router.get("/requests", response_model=List[AuthorRequestRead])
def list_my_requests(
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    author = _get_own_author_or_400(user, session)
    artifacts = session.exec(
        select(Artifact).where(Artifact.author_id == author.id)
    ).all()
    artifact_ids = [a.id for a in artifacts]
    if not artifact_ids:
        return []
    requests = session.exec(
        select(RequestModel).where(RequestModel.artifact_id.in_(artifact_ids))
    ).all()
    result = []
    for req in requests:
        artifact = next((a for a in artifacts if a.id == req.artifact_id), None)
        partner = req.partner
        result.append(
            AuthorRequestRead(
                id=req.id,
                artifact_id=req.artifact_id,
                artifact_title=artifact.title if artifact else "Unknown",
                partner_id=req.partner_id,
                partner_name=partner.name if partner else "Unknown",
                type=req.type,
                status=req.status,
                created_at=req.created_at,
            )
        )
    return result


@router.post("/requests/{request_id}/decision", response_model=AuthorRequestRead)
def decide_on_request(
    request_id: int,
    data: RequestDecision,
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    author = _get_own_author_or_400(user, session)
    req = session.get(RequestModel, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    artifact = session.get(Artifact, req.artifact_id)
    if not artifact or artifact.author_id != author.id:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.type != "full_text":
        raise HTTPException(
            status_code=400, detail="Only full_text requests can be decided by author"
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
    partner = req.partner
    return AuthorRequestRead(
        id=req.id,
        artifact_id=req.artifact_id,
        artifact_title=artifact.title,
        partner_id=req.partner_id,
        partner_name=partner.name if partner else "Unknown",
        type=req.type,
        status=req.status,
        created_at=req.created_at,
    )


@router.get("/internships", response_model=List[dict])
def get_my_internships(
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    """Получить все приглашения на стажировку для текущего автора."""
    author = _get_own_author_or_400(user, session)
    artifacts = session.exec(
        select(Artifact).where(Artifact.author_id == author.id)
    ).all()
    artifact_ids = [a.id for a in artifacts]
    if not artifact_ids:
        return []
    internships = session.exec(
        select(Internship).where(Internship.artifact_id.in_(artifact_ids))
    ).all()

    result = []
    for inv in internships:
        artifact = next((a for a in artifacts if a.id == inv.artifact_id), None)
        result.append({
            "id": inv.id,
            "artifact_id": inv.artifact_id,
            "partner_id": inv.partner_id,
            "partner_name": inv.partner.name if inv.partner else None,
            "status": inv.status,
            "student_name": inv.student_name,
            "created_at": inv.created_at,
            "response_date": inv.response_date,
            "artifact_title": artifact.title if artifact else None,
        })
    return result


@router.post("/internships/{internship_id}/respond", response_model=dict)
def respond_to_internship(
    internship_id: int,
    data: InternshipResponse,
    user: User = Depends(require_role("author")),
    session: Session = Depends(get_session),
):
    """Автор принимает или отклоняет приглашение на стажировку."""
    author = _get_own_author_or_400(user, session)
    inv = session.get(Internship, internship_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Internship not found")
    artifact = session.get(Artifact, inv.artifact_id)
    if not artifact or artifact.author_id != author.id:
        raise HTTPException(status_code=404, detail="Internship not found")
    if inv.status != "sent":
        raise HTTPException(
            status_code=400, detail=f"Cannot respond to internship in status '{inv.status}'"
        )
    inv.status = "accepted" if data.accept else "rejected"
    inv.response_date = datetime.utcnow()
    session.add(inv)
    session.commit()
    session.refresh(inv)
    return {"id": inv.id, "status": inv.status}