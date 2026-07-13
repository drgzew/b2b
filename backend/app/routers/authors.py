from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Author, User
from ..schemas import AuthorJobStatusUpdate, AuthorPublicRead, AuthorRead, TumguSsoLogin
from ..security import require_role
from ..sso import parse_tumgu_profile

router = APIRouter(prefix="/authors", tags=["authors"])


@router.post("/sso/tumgu", response_model=AuthorRead)
def login_via_tumgu_email(
    data: TumguSsoLogin,
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    """Имитирует вход автора через университетскую почту: 'парсит' ФИО, фото,
    дату рождения и направление (см. app/sso.py) и создаёт/обновляет профиль.
    Сейчас вызывается куратором/админом в момент занесения работы в систему —
    отдельного личного кабинета и самостоятельного логина для авторов в пилоте нет
    (см. открытый вопрос в docs/api-contract.md).
    Реальный SSO подключается заменой тела parse_tumgu_profile(), сам эндпоинт не меняется.
    """
    profile = parse_tumgu_profile(data.email)

    author = session.exec(select(Author).where(Author.email == data.email)).first()
    if author:
        author.full_name = profile["full_name"]
        author.photo_url = profile["photo_url"]
        author.birth_date = profile["birth_date"]
        author.program = profile["program"]
    else:
        author = Author(email=data.email, **profile)

    session.add(author)
    session.commit()
    session.refresh(author)
    return AuthorRead(**author.dict())


@router.get("", response_model=List[AuthorRead])
def list_authors(
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    authors = session.exec(select(Author)).all()
    return [AuthorRead(**a.dict()) for a in authors]


def _get_author_or_404(author_id: int, session: Session) -> Author:
    author = session.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@router.get("/{author_id}", response_model=AuthorRead)
def get_author(
    author_id: int,
    user: User = Depends(require_role("curator", "admin", "partner")),
    session: Session = Depends(get_session),
):
    """Кликабельный профиль автора — доступен из карточки артефакта.
    Партнёру (role == 'partner') отдаём урезанный набор полей: без email и даты рождения,
    только то, что нужно для решения о стажировке/НИОКР.
    Формально response_model один и тот же (AuthorRead), но для партнёра чувствительные
    поля обнуляются — так фронту не нужно дёргать два разных эндпоинта в зависимости от роли.
    """
    author = _get_author_or_404(author_id, session)

    if user.role == "partner":
        public = AuthorPublicRead(
            id=author.id,
            full_name=author.full_name,
            photo_url=author.photo_url,
            program=author.program,
            job_status=author.job_status,
        )
        return AuthorRead(
            id=public.id,
            email=None,
            full_name=public.full_name,
            photo_url=public.photo_url,
            birth_date=None,
            program=public.program,
            job_status=public.job_status,
        )

    return AuthorRead(**author.dict())


@router.patch("/{author_id}/job-status", response_model=AuthorRead)
def update_job_status(
    author_id: int,
    data: AuthorJobStatusUpdate,
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    """Куратор/админ обновляет статус автора (например, со слов автора)."""
    valid_statuses = {"searching", "not_searching", "employed"}
    if data.job_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"job_status must be one of {sorted(valid_statuses)}",
        )

    author = _get_author_or_404(author_id, session)
    author.job_status = data.job_status
    session.add(author)
    session.commit()
    session.refresh(author)
    return AuthorRead(**author.dict())