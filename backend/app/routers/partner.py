from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
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
    Tag,
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
    SubscriptionUpdate,
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
    return PartnerRead(
        id=partner.id,
        name=partner.name,
        contact_email=partner.contact_email,
    )


@router.get("/subscriptions", response_model=List[SubscriptionRead])
def list_subscriptions(
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)
    return [
        SubscriptionRead(
            id=s.id,
            name=s.name,
            tags=[t.name for t in s.tags],
            description=s.description,
        )
        for s in partner.subscriptions
    ]


@router.put("/subscriptions", response_model=List[SubscriptionRead])
def replace_subscriptions(
    data: SubscriptionUpdate,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    """Заменяет весь набор подписок партнёра на присланный."""
    partner = _get_partner_or_404(user, session)

    # Удаляем старые подписки
    for subscription in list(partner.subscriptions):
        for item in list(subscription.digest_items):
            session.delete(item)
        session.delete(subscription)
    session.commit()

    created: List[Subscription] = []
    for topic in data.subscriptions:
        subscription = Subscription(
            partner_id=partner.id,
            name=topic.name,
            description=topic.description,
        )
        subscription.tags = session.exec(
            select(Tag).where(Tag.name.in_(topic.tags))
        ).all()
        session.add(subscription)
        created.append(subscription)
    session.commit()

    for subscription in created:
        session.refresh(subscription)

    return [
        SubscriptionRead(
            id=s.id,
            name=s.name,
            tags=[t.name for t in s.tags],
            description=s.description,
        )
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
    if not subscription or subscription.partner_id != partner.id:
        raise HTTPException(status_code=404, detail="Subscription not found")

    subscription_tags = {t.name for t in subscription.tags}

    # 🔥 ЯВНО ЗАГРУЖАЕМ ТЕГИ АРТЕФАКТОВ
    artifacts = session.exec(
        select(Artifact)
        .where(Artifact.curator_status == "approved")
        .options(selectinload(Artifact.tags))
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
        raise HTTPException(
            status_code=400,
            detail="Full text is already accessible, use GET /partner/artifacts/{id}/read",
        )

    req = RequestModel(
        artifact_id=data.artifact_id,
        partner_id=partner.id,
        type=data.type,
    )
    session.add(req)
    session.commit()
    session.refresh(req)
    return RequestRead(**req.dict())


# --- Стажировки ---


def _to_internship_read(internship: Internship) -> InternshipRead:
    return InternshipRead(
        **internship.dict(),
        artifact_title=internship.artifact.title if internship.artifact else None,
        artifact=to_artifact_read(internship.artifact) if internship.artifact else None,
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
    partner = _get_partner_or_404(user, session)

    artifact = session.exec(
        select(Artifact)
        .where(Artifact.id == data.artifact_id)
        .options(selectinload(Artifact.author))
    ).first()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    author_name = (
        artifact.author.full_name
        if artifact.author
        else "Автор не указан"
    )

    internship = Internship(
        artifact_id=artifact.id,
        partner_id=partner.id,
        student_name=author_name,
    )

    session.add(internship)
    session.commit()
    session.refresh(internship)

    internship.artifact = artifact

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
            Favorite.partner_id == partner.id,
            Favorite.artifact_id == data.artifact_id,
        )
    ).first()
    if existing:
        return FavoriteRead(**existing.dict(), artifact=to_artifact_read(artifact))

    favorite = Favorite(artifact_id=data.artifact_id, partner_id=partner.id)
    session.add(favorite)
    session.commit()
    session.refresh(favorite)
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