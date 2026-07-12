from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Partner, User
from ..schemas import PartnerCreate, PartnerRead, UserCreate, UserRead
from ..security import hash_password, require_role

router = APIRouter(prefix="/admin", tags=["admin"])

# Примечание про "все права": вместо дублирования каждого эндпоинта куратора
# и партнёра под /admin, роль "admin" добавлена в require_role(...) тех
# эндпоинтов, где это осмысленно (см. routers/curator.py, routers/authors.py) —
# админ дёргает те же ручки, что и куратор, без отдельной копии кода.
# Здесь — только то, что специфично именно для администратора: управление
# учётными записями и партнёрами.


@router.get("/users", response_model=List[UserRead])
def list_users(
    user: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    users = session.exec(select(User)).all()
    return [UserRead(**u.dict(exclude={"password_hash"})) for u in users]


@router.post("/users", response_model=UserRead)
def create_user(
    data: UserCreate,
    user: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    valid_roles = {"partner", "curator", "admin", "author"}
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"role must be one of {sorted(valid_roles)}")
    if data.role == "partner" and not data.partner_id:
        raise HTTPException(status_code=400, detail="partner_id is required for role 'partner'")
    if data.role == "author" and not data.author_id:
        raise HTTPException(status_code=400, detail="author_id is required for role 'author'")

    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    new_user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        partner_id=data.partner_id,
        author_id=data.author_id,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return UserRead(**new_user.dict(exclude={"password_hash"}))


@router.get("/partners", response_model=List[PartnerRead])
def list_partners(
    user: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    partners = session.exec(select(Partner)).all()
    return [PartnerRead(**p.dict()) for p in partners]


@router.post("/partners", response_model=PartnerRead)
def create_partner(
    data: PartnerCreate,
    user: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    partner = Partner(**data.dict())
    session.add(partner)
    session.commit()
    session.refresh(partner)
    return PartnerRead(**partner.dict())
