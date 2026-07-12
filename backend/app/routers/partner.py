from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

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
    RequestCreate,
    RequestRead,
    SubscriptionRead,
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
    return RequestRead(**req.dict())


# --- Стажировки ---

_INTERNSHIP_STATUSES = {"sent", "accepted", "in_progress", "rejected", "completed"}


def _get_own_internship_or_404(internship_id: int, partner: Partner, session: Session) -> Internship:
    internship = session.get(Internship, internship_id)
    # Проверяем принадлежность партнёру, а не только существование записи —
    # тот же принцип, что и в get_digest: партнёр не должен читать/менять
    # чужие стажировки, просто подставив чужой id.
    if not internship or internship.partner_id != partner.id:
        raise HTTPException(status_code=404, detail="Internship not found")
    return internship


@router.get("/internships", response_model=List[InternshipRead])
def list_internships(
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)
    internships = session.exec(
        select(Internship).where(Internship.partner_id == partner.id)
    ).all()
    return [InternshipRead(**i.dict()) for i in internships]


@router.post("/internships", response_model=InternshipRead)
def create_internship(
    data: InternshipCreate,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)

    artifact = session.get(Artifact, data.artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    student_name = data.student_name
    if not student_name:
        if not artifact.author:
            raise HTTPException(
                status_code=400,
                detail="student_name is required: artifact has no linked author",
            )
        student_name = artifact.author.full_name

    internship = Internship(
        artifact_id=data.artifact_id,
        partner_id=partner.id,
        student_name=student_name,
    )
    session.add(internship)
    session.commit()
    session.refresh(internship)
    return InternshipRead(**internship.dict())


@router.patch("/internships/{internship_id}/status", response_model=InternshipRead)
def update_internship_status(
    internship_id: int,
    data: InternshipStatusUpdate,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    if data.status not in _INTERNSHIP_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of {sorted(_INTERNSHIP_STATUSES)}",
        )

    partner = _get_partner_or_404(user, session)
    internship = _get_own_internship_or_404(internship_id, partner, session)

    internship.status = data.status
    internship.response_date = datetime.utcnow()
    session.add(internship)
    session.commit()
    session.refresh(internship)
    return InternshipRead(**internship.dict())


# --- Избранное ---

def _get_own_favorite_or_404(favorite_id: int, partner: Partner, session: Session) -> Favorite:
    favorite = session.get(Favorite, favorite_id)
    if not favorite or favorite.partner_id != partner.id:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return favorite


@router.get("/favorites", response_model=List[FavoriteRead])
def list_favorites(
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)
    favorites = session.exec(
        select(Favorite).where(Favorite.partner_id == partner.id)
    ).all()
    return [FavoriteRead(**f.dict()) for f in favorites]


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
        raise HTTPException(status_code=409, detail="Artifact already in favorites")

    favorite = Favorite(artifact_id=data.artifact_id, partner_id=partner.id)
    session.add(favorite)
    session.commit()
    session.refresh(favorite)
    return FavoriteRead(**favorite.dict())


@router.delete("/favorites/{favorite_id}", status_code=204)
def remove_favorite(
    favorite_id: int,
    user: User = Depends(require_role("partner")),
    session: Session = Depends(get_session),
):
    partner = _get_partner_or_404(user, session)
    favorite = _get_own_favorite_or_404(favorite_id, partner, session)

    session.delete(favorite)
    session.commit()
