from datetime import date, datetime
from typing import List, Optional

from sqlmodel import SQLModel


# --- Автор ---

class AuthorRead(SQLModel):
    """Полный профиль — для куратора/админа."""

    id: int
    email: Optional[str]  # null, если профиль отдан партнёру (см. GET /authors/{id})
    full_name: str
    photo_url: Optional[str]
    birth_date: Optional[date]
    program: Optional[str]
    job_status: str  # searching | not_searching | employed


class AuthorPublicRead(SQLModel):
    """Урезанный профиль — для партнёра. Без email и даты рождения:
    партнёру для решения о стажировке/НИОКР это не нужно, а хранить
    у себя лишние персональные данные партнёру не стоит (принцип
    минимизации данных, перекликается с рисками "утечка данных" из
    исходного документа продукта)."""

    id: int
    full_name: str
    photo_url: Optional[str]
    program: Optional[str]
    job_status: str


class AuthorJobStatusUpdate(SQLModel):
    job_status: str  # searching | not_searching | employed


class TumguSsoLogin(SQLModel):
    """Запрос на 'вход через почту ТюмГУ'. Пока обёртка над моком
    (см. app/sso.py) — тело функции заменится на реальный SSO позже,
    форма запроса при этом не изменится."""

    email: str


# --- Артефакт ---

class ArtifactCreate(SQLModel):
    title: str
    type: str
    annotation: str
    file_path: Optional[str] = None
    curator_status: str = "draft"
    access_level: str = "none"
    author_id: Optional[int] = None
    tags: List[str] = []  # имена тегов; несуществующие теги будут созданы


class ArtifactRead(SQLModel):
    id: int
    title: str
    type: str
    annotation: str
    file_path: Optional[str]
    curator_status: str
    access_level: str
    created_at: datetime
    tags: List[str] = []
    # Кликабельная ссылка на профиль автора: id + мини-превью для списков.
    # Полный профиль — через GET /authors/{id} (или /authors/{id}/public для партнёра).
    author_id: Optional[int] = None
    author_name: Optional[str] = None


# --- Аутентификация ---

class LoginRequest(SQLModel):
    email: str
    password: str


class TokenResponse(SQLModel):
    access_token: str
    role: str


# --- Партнёр ---

class PartnerRead(SQLModel):
    id: int
    name: str
    contact_email: str


class SubscriptionRead(SQLModel):
    id: int
    name: Optional[str]
    tags: List[str]


class DigestEntry(SQLModel):
    artifact: ArtifactRead
    relevance: float


class RequestCreate(SQLModel):
    artifact_id: int
    type: str  # full_text | internship | rnd


class RequestRead(SQLModel):
    id: int
    artifact_id: int
    partner_id: int
    type: str
    status: str
    created_at: datetime


# --- Куратор ---

class TagsUpdate(SQLModel):
    tag_ids: List[int]


class RequestStatusUpdate(SQLModel):
    status: str  # in_progress | done


# --- Админ ---

class UserRead(SQLModel):
    id: int
    email: str
    role: str
    partner_id: Optional[int]


class UserCreate(SQLModel):
    email: str
    password: str
    role: str  # partner | curator | admin
    partner_id: Optional[int] = None  # обязательно для role == "partner"


class PartnerCreate(SQLModel):
    name: str
    contact_email: str
