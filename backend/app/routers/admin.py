import json
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlmodel import Session, select

from ..db import get_session
from ..importer import import_artifacts
from ..models import Author, Partner, User
from ..schemas import ImportResult, PartnerCreate, PartnerRead, UserCreate, UserRead
from ..security import hash_password, require_role

router = APIRouter(prefix="/admin", tags=["admin"])

# Примечание про "все права": вместо дублирования каждого эндпоинта куратора
# и партнёра под /admin, роль "admin" добавлена в require_role(...) тех
# эндпоинтов, где это осмысленно (см. routers/curator.py, routers/authors.py) —
# админ дёргает те же ручки, что и куратор, без отдельной копии кода.
# Здесь — только то, что специфично именно для администратора: управление
# учётными записями и партнёрами.


@router.post("/import", response_model=ImportResult)
async def import_artifacts_endpoint(
    file: UploadFile = File(..., description="normalized.json от parsing/scripts/normalize.py"),
    wipe: bool = Query(
        default=False,
        description="Удалить все существующие артефакты/теги перед импортом. Осторожно — необратимо.",
    ),
    user: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """То же самое, что раньше делалось только через консоль
    (`python -m parsing.scripts.import --file ... [--wipe]`) — теперь можно
    вызвать из интерфейса админа: выбрать normalized.json и нажать кнопку.

    Логика та же самая (app/importer.py), что использует и CLI-скрипт —
    результат идентичен независимо от способа запуска.
    """
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Ожидается JSON-файл (normalized.json)")

    raw = await file.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Файл повреждён или не JSON: {e}")

    if isinstance(data, dict) and "artifacts" in data:
        artifacts_data = data["artifacts"]
    elif isinstance(data, list):
        artifacts_data = data
    else:
        raise HTTPException(
            status_code=400,
            detail="Неизвестный формат: ожидается список артефактов или {'artifacts': [...]}",
        )

    if not artifacts_data:
        raise HTTPException(status_code=400, detail="Файл не содержит артефактов")

    stats = import_artifacts(artifacts_data, session, wipe=wipe)

    return ImportResult(
        total=stats["total"],
        imported=stats["imported"],
        skipped=stats["skipped"],
        errors=stats["errors"],
        error_details=stats["error_details"],
        tags_created=stats["tags_created"],
        tags_existing=stats["tags_existing"],
        with_annotation=stats["with_annotation"],
        with_tags=stats["with_tags"],
    )


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
        raise HTTPException(
            status_code=400, detail=f"role must be one of {sorted(valid_roles)}"
        )

    if data.role == "partner" and not data.partner_id:
        raise HTTPException(
            status_code=400, detail="partner_id is required for role 'partner'"
        )
    if data.role == "author" and not data.author_id:
        raise HTTPException(
            status_code=400, detail="author_id is required for role 'author'"
        )

    # Проверяем существование связанных записей заранее — иначе FK-нарушение
    # уронит запрос в 500 без внятного сообщения.
    if data.partner_id and not session.get(Partner, data.partner_id):
        raise HTTPException(status_code=400, detail=f"Partner {data.partner_id} not found")
    if data.author_id and not session.get(Author, data.author_id):
        raise HTTPException(status_code=400, detail=f"Author {data.author_id} not found")

    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

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