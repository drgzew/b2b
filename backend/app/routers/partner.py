from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..access import has_read_access
from ..converters import to_artifact_read
from ..db import get_session
from ..matching import match_by_tags
from ..models import (
    Artifact,
    Favorite,
    Internship,
    Partner,
    Request as RequestModel,
    Subscription,
    User,
)
from ..schemas import (
    DigestEntry,
    FavoriteCreate,
    FavoriteRead,
    InternshipCreate,
    InternshipRead,
    InternshipStatusUpdate,
    PartnerRead,
    ReadAccessResponse,
    RequestCreate,
    RequestRead,
    SubscriptionRead,
)
from ..security import require_role
from ..workflows import can_transition

router = APIRouter(prefix="/partner", tags=["partner"])


def _get_partner_or_404(user: User, session: Session) -> Partner:
    if not user.partner_id:
        raise HTTPException(status_code=400, detail="User is not linked to a partner")
    partner = session.get(Partner, user.partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return partner


@router.get("/me", response_model=PartnerRead)
def get_me(
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)
    return PartnerRead(id=partner.id, name=partner.name, contact_email=partner.contact_email)


@router.get("/subscriptions", response_model=List[SubscriptionRead])
def list_subscriptions(
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)
    return [
        SubscriptionRead(id=s.id, name=s.name, tags=[t.name for t in s.tags])
        for s in partner.subscriptions
    ]


@router.get("/subscriptions/{subscription_id}/digest", response_model=List[DigestEntry])
def get_digest(
    subscription_id: int,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)

    subscription = session.get(Subscription, subscription_id)
    # Проверяем не только "существует ли подписка", но и что она принадлежит
    # именно этому партнёру — иначе один партнёр мог бы читать дайджест другого,
    # просто подставив чужой id (это как раз риск "один партнёр получает
    # преимущество перед другим" из вашего документа).
    if not subscription or subscription.partner_id != partner.id:
        raise HTTPException(status_code=404, detail="Subscription not found")

    subscription_tags = {t.name for t in subscription.tags}

    artifacts = session.exec(
        select(Artifact).where(Artifact.curator_status == "approved")
    ).all()

    entries: List[DigestEntry] = []
    for artifact in artifacts:
        artifact_tags = {t.name for t in artifact.tags}
        relevance = match_by_tags(subscription_tags, artifact_tags)
        if relevance > 0:
            entries.append(
                DigestEntry(
                    artifact=to_artifact_read(artifact),
                    relevance=round(relevance, 4),
                    can_read=has_read_access(session, artifact, partner.id),
                )
            )

    entries.sort(key=lambda e: e.relevance, reverse=True)
    return entries


@router.get("/artifacts/{artifact_id}/read", response_model=ReadAccessResponse)
def read_artifact(
    artifact_id: int,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    """Кнопка 'Запросить полный текст' в состоянии 'уже доступно': сразу
    отдаёт, куда вести партнёра — переход по ссылке для ВКР, открытие PDF
    для статьи/доклада (см. ReadAccessResponse). Если доступа ещё нет —
    403 с явной подсказкой создать запрос через POST /requests."""
    partner = _get_partner_or_404(user, session)

    artifact = session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    if not has_read_access(session, artifact, partner.id):
        raise HTTPException(
            status_code=403,
            detail="Full text is not available yet. Submit a request via POST /partner/requests.",
        )

    mode = "redirect" if artifact.type == "vkr" else "pdf"
    return ReadAccessResponse(mode=mode, url=artifact.file_path)


@router.post("/requests", response_model=RequestRead)
def create_request(
    data: RequestCreate,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)

    artifact = session.get(Artifact, data.artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    if data.type == "full_text" and has_read_access(session, artifact, partner.id):
        # Не создаём запрос, если читать уже можно — тогда правильный путь
        # для фронта GET /artifacts/{id}/read, а не ждать чьего-то решения.
        raise HTTPException(
            status_code=400,
            detail="Full text is already accessible, use GET /partner/artifacts/{id}/read",
        )

    req = RequestModel(artifact_id=data.artifact_id, partner_id=partner.id, type=data.type)
    session.add(req)
    session.commit()
    session.refresh(req)
    return RequestRead(**req.dict())


# --- Стажировки ---

def _to_internship_read(internship: Internship) -> InternshipRead:
    return InternshipRead(
        **internship.dict(),
        artifact_title=internship.artifact.title if internship.artifact else None,
    )


@router.get("/internships", response_model=List[InternshipRead])
def list_internships(
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)
    return [_to_internship_read(i) for i in partner.internships]


@router.post("/internships", response_model=InternshipRead)
def create_internship(
    data: InternshipCreate,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    """Партнёр приглашает автора конкретного артефакта на стажировку.

    Не было в исходном ТЗ (там было только 5 эндпоинтов без создания) —
    добавлено по уточнению, иначе список стажировок нечем было бы наполнить
    кроме как вручную в БД.
    """
    partner = _get_partner_or_404(user, session)

    artifact = session.get(Artifact, data.artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    internship = Internship(
        artifact_id=data.artifact_id,
        partner_id=partner.id,
        student_name=data.student_name,
    )
    session.add(internship)
    session.commit()
    session.refresh(internship)
    return _to_internship_read(internship)


@router.patch("/internships/{internship_id}/status", response_model=InternshipRead)
def update_internship_status(
    internship_id: int,
    data: InternshipStatusUpdate,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)

    internship = session.get(Internship, internship_id)
    # Тот же принцип, что и у Subscription/digest: чужая запись — 404, не 403,
    # чтобы не подтверждать сам факт её существования.
    if not internship or internship.partner_id != partner.id:
        raise HTTPException(status_code=404, detail="Internship not found")

    if not can_transition(internship.status, data.status):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition internship from '{internship.status}' to '{data.status}'",
        )

    internship.status = data.status
    internship.response_date = datetime.utcnow()
    session.add(internship)
    session.commit()
    session.refresh(internship)
    return _to_internship_read(internship)


# --- Избранное ---

@router.get("/favorites", response_model=List[FavoriteRead])
def list_favorites(
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)
    return [
        FavoriteRead(**f.dict(), artifact=to_artifact_read(f.artifact))
        for f in partner.favorites
    ]


@router.post("/favorites", response_model=FavoriteRead)
def add_favorite(
    data: FavoriteCreate,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)

    artifact = session.get(Artifact, data.artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    existing = session.exec(
        select(Favorite).where(
            Favorite.partner_id == partner.id, Favorite.artifact_id == data.artifact_id
        )
    ).first()
    if existing:
        # Идемпотентно: повторное добавление того же артефакта не создаёт дубль,
        # просто возвращает уже существующую запись.
        return FavoriteRead(**existing.dict(), artifact=to_artifact_read(artifact))

    favorite = Favorite(artifact_id=data.artifact_id, partner_id=partner.id)
    session.add(favorite)
    session.commit()
    session.refresh(favorite)
    # commit() выше "протухает" все объекты сессии, включая уже загруженный
    # artifact — без refresh() его .dict() внутри to_artifact_read() тихо
    # вернёт пустой словарь вместо реальных полей (поймано на тестах).
    session.refresh(artifact)
    return FavoriteRead(**favorite.dict(), artifact=to_artifact_read(artifact))


@router.delete("/favorites/{favorite_id}", status_code=204)
def remove_favorite(
    favorite_id: int,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)

    favorite = session.get(Favorite, favorite_id)
    if not favorite or favorite.partner_id != partner.id:
        raise HTTPException(status_code=404, detail="Favorite not found")

    session.delete(favorite)
    session.commit()
