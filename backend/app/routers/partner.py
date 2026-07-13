from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..converters import to_artifact_read
from ..db import get_session
from ..matching import match_by_tags
from ..models import Favorite, Artifact, Partner, Request as RequestModel, Subscription, Tag, User
from ..schemas import (
    ArtifactShortRead,
    DigestEntry,
    PartnerRead,
    PartnerShortRead,
    RequestCreate,
    RequestRead,
    SubscriptionRead,
    SubscriptionsUpdate,
    FavoriteCreate,
    FavoriteArtifactRead
)
from ..security import require_role

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


@router.put("/subscriptions", response_model=List[SubscriptionRead])
def replace_subscriptions(
    data: SubscriptionsUpdate,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    """Заменяет весь набор подписок партнёра на присланный.

    Фронт («Управление подписками») отдаёт итоговый список тем целиком,
    поэтому проще удалить прежние подписки и создать новые, чем считать дельту.
    """
    partner = _get_partner_or_404(user, session)

    # Удаляем прежние подписки партнёра вместе с их элементами дайджеста,
    # которые ссылаются на подписку по внешнему ключу.
    for subscription in list(partner.subscriptions):
        for item in list(subscription.digest_items):
            session.delete(item)
        session.delete(subscription)
    session.commit()

    created: List[Subscription] = []
    for topic in data.subscriptions:
        subscription = Subscription(partner_id=partner.id, name=topic.name)
        # Берём только уже существующие теги по имени — каталог тем фиксированный,
        # все теги заведены сидом; неизвестные молча пропускаем.
        subscription.tags = session.exec(
            select(Tag).where(Tag.name.in_(topic.tags))
        ).all()
        session.add(subscription)
        created.append(subscription)
    session.commit()

    for subscription in created:
        session.refresh(subscription)

    return [
        SubscriptionRead(id=s.id, name=s.name, tags=[t.name for t in s.tags])
        for s in created
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
                DigestEntry(artifact=to_artifact_read(artifact), relevance=round(relevance, 4))
            )

    entries.sort(key=lambda e: e.relevance, reverse=True)
    return entries


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

    req = RequestModel(artifact_id=data.artifact_id, partner_id=partner.id, type=data.type)
    session.add(req)
    session.commit()
    session.refresh(req)
    # RequestRead ждёт вложенные artifact/partner (как в GET /curator/requests),
    # поэтому собираем ответ вручную, а не через req.dict().
    return RequestRead(
        id=req.id,
        artifact=ArtifactShortRead(id=artifact.id, title=artifact.title),
        partner=PartnerShortRead(id=partner.id, name=partner.name),
        type=req.type,
        status=req.status,
        created_at=req.created_at,
    )

@router.post("/favorites")
def add_favorite(
    data: FavoriteCreate,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)

    existing = session.exec(
        select(Favorite).where(
            Favorite.partner_id == partner.id,
            Favorite.artifact_id == data.artifact_id,
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Artifact already in favorites"
        )

    artifact = session.get(Artifact, data.artifact_id)

    if not artifact:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found"
        )

    favorite = Favorite(
        partner_id=partner.id,
        artifact_id=data.artifact_id,
    )

    session.add(favorite)
    session.commit()
    session.refresh(favorite)

    return favorite

@router.get("/favorites", response_model=List[FavoriteArtifactRead])
def get_favorites(
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)

    favorites = session.exec(
        select(Favorite)
        .where(Favorite.partner_id == partner.id)
    ).all()

    result = []

    for favorite in favorites:
        artifact = favorite.artifact

        result.append(
            FavoriteArtifactRead(
                id=favorite.id,
                artifact=to_artifact_read(artifact)
            )
        )

    return result

@router.delete("/favorites/{favorite_id}")
def remove_favorite(
    favorite_id: int,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)

    favorite = session.get(Favorite, favorite_id)

    if not favorite:
        raise HTTPException(
            status_code=404,
            detail="Favorite not found"
        )

    if favorite.partner_id != partner.id:
        raise HTTPException(
            status_code=403,
            detail="Not your favorite"
        )

    session.delete(favorite)
    session.commit()

    return {"message": "Removed from favorites"}