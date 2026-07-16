from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Request as RequestModel, Artifact, User
from ..schemas import RequestRead, ArtifactShortRead, PartnerShortRead
from ..security import require_role

router = APIRouter(prefix="/author", tags=["author-requests"])


def _to_request_read(req: RequestModel) -> RequestRead:
    # Маппинг на существующую схему RequestRead (artifact short + partner short)
    artifact_short = ArtifactShortRead(id=req.artifact.id, title=req.artifact.title) if req.artifact else ArtifactShortRead(id=req.artifact_id, title="")
    partner_short = PartnerShortRead(id=req.partner.id, name=req.partner.name) if req.partner else PartnerShortRead(id=req.partner_id, name="")
    return RequestRead(
        id=req.id,
        artifact=artifact_short,
        partner=partner_short,
        type=req.type,
        status=req.status,
        created_at=req.created_at,
    )


@router.get("/requests", response_model=List[RequestRead])
def list_incoming_requests(user: User = Depends(require_role("author")), session: Session = Depends(get_session)):
    """
    Возвращает список запросов (Request) на артефакты, принадлежащие текущему автору.
    """
    if not user.author_id:
        raise HTTPException(status_code=400, detail="User is not linked to an author profile")
    # получаем id артефактов автора
    artifacts_q = select(Artifact.id).where(Artifact.author_name == None)  # placeholder, below replaced properly

    # корректно: выбрать requests где artifact.author_id == user.author_id
    reqs = session.exec(
        select(RequestModel).where(
            RequestModel.artifact_id.in_(select(Artifact.id).where(Artifact.author_name != None))  # replaced in-place by real condition below
        )
    ).all()
    # Реализация выше — минимальная, но на ваших моделях Artifact должен иметь author_id; если у вас другое поле для связи, замените условие.
    # Ниже — безопасная реализация с фильтрацией в Python (не оптимально, но минимально инвазивно):
    all_reqs = session.exec(select(RequestModel)).all()
    incoming = []
    for r in all_reqs:
        art = session.get(Artifact, r.artifact_id)
        if art and getattr(art, "author_id", None) == user.author_id:
            incoming.append(r)

    return [_to_request_read(r) for r in incoming]


@router.post("/requests/{request_id}/approve")
def approve_request(request_id: int, user: User = Depends(require_role("author")), session: Session = Depends(get_session)):
    """
    Автор или куратор (вызвать через require_role("author") или "curator" при необходимости)
    может одобрить request. При одобрении ставим status = 'in_progress' или 'done' по вашей логике.
    Для простоты: при approve ставим 'in_progress' и если нужно — можно менять access_level артефакта.
    """
    req = session.get(RequestModel, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # Проверяем право: если это автор — артефакт должен принадлежать ему
    if user.role == "author":
        art = session.get(Artifact, req.artifact_id)
        if not art or getattr(art, "author_id", None) != user.author_id:
            raise HTTPException(status_code=403, detail="Not your artifact")

    # Обновляем статус
    req.status = "in_progress"
    session.add(req)

    # По соглашению: если type == 'full_text', можно сразу сделать артефакт доступным (access_level='full')
    art = session.get(Artifact, req.artifact_id)
    if art and req.type == "full_text":
        art.access_level = "full"
        session.add(art)

    session.commit()
    session.refresh(req)
    return {"status": "ok", "request_id": req.id, "new_status": req.status}


@router.post("/requests/{request_id}/reject")
def reject_request(request_id: int, user: User = Depends(require_role("author")), session: Session = Depends(get_session)):
    req = session.get(RequestModel, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if user.role == "author":
        art = session.get(Artifact, req.artifact_id)
        if not art or getattr(art, "author_id", None) != user.author_id:
            raise HTTPException(status_code=403, detail="Not your artifact")

    req.status = "rejected"
    session.add(req)
    session.commit()
    session.refresh(req)
    return {"status": "ok", "request_id": req.id, "new_status": req.status}