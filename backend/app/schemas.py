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


class TeacherRead(SQLModel):
    """Демо-профиль преподавателя (руководителя ВКР) — кликабельный, как и Author."""

    id: int
    full_name: str
    email: str
    department: str
    position: str


# --- Артефакт ---

class ArtifactCreate(SQLModel):
    title: str
    type: str
    annotation: str
    file_path: Optional[str] = None
    curator_status: str = "draft"
    read_policy: str = "requires_approval"  # open | requires_approval — запрет по умолчанию
    author_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    tags: List[str] = []  # имена тегов; несуществующие теги будут созданы


class ArtifactRead(SQLModel):
    id: int
    title: str
    type: str
    annotation: str
    file_path: Optional[str]
    curator_status: str
    read_policy: str  # open | requires_approval
    created_at: datetime
    tags: List[str] = []
    # Кликабельные ссылки на профили: id + имя для списков.
    # Полный профиль — через GET /authors/{id} или GET /teachers/{id}.
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    supervisor_id: Optional[int] = None
    supervisor_name: Optional[str] = None


class ReadPolicyUpdate(SQLModel):
    read_policy: str  # open | requires_approval


class ReadAccessResponse(SQLModel):
    """Ответ на 'открыть полный текст': куда именно вести партнёра.

    mode == "redirect" — для ВКР: file_path это внешняя ссылка (например, на
    репозиторий ВКР ТюмГУ), фронт делает переход по ней.
    mode == "pdf" — для статьи/доклада: file_path это ссылка на PDF,
    фронт открывает его во встроенном просмотрщике/новой вкладке.
    """

    mode: str  # redirect | pdf
    url: Optional[str]


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
    # Может ли именно этот партнёр прямо сейчас открыть полный текст —
    # без этого фронту пришлось бы отдельным запросом на каждый артефакт
    # проверять доступ, чтобы решить, какую кнопку показать.
    can_read: bool


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
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None


class RequestDecision(SQLModel):
    approve: bool


class AuthorRequestRead(SQLModel):
    """Запрос на чтение — как его видит автор/куратор: с именем компании
    и названием работы, а не голыми id (см. требование "в запросе будет
    отображаться компания... и кнопка разрешить/нет")."""

    id: int
    artifact_id: int
    artifact_title: str
    partner_id: int
    partner_name: str
    status: str
    created_at: datetime


# --- Стажировки ---

class InternshipRead(SQLModel):
    id: int
    artifact_id: int
    partner_id: int
    status: str  # sent | accepted | in_progress | rejected | completed
    student_name: str
    created_at: datetime
    response_date: Optional[datetime]
    # Не в исходном ТЗ, но добавлено для удобства фронта — не нужно делать
    # отдельный запрос за названием артефакта ради списка приглашений.
    artifact_title: Optional[str] = None


class InternshipCreate(SQLModel):
    artifact_id: int
    student_name: str


class InternshipStatusUpdate(SQLModel):
    status: str  # accepted | in_progress | rejected | completed


# --- Избранное ---

class FavoriteRead(SQLModel):
    id: int
    artifact_id: int
    partner_id: int
    added_at: datetime
    artifact: ArtifactRead


class FavoriteCreate(SQLModel):
    artifact_id: int


# --- Куратор ---

class TagsUpdate(SQLModel):
    tag_ids: List[int]


class TagRead(SQLModel):
    id: int
    name: str


class RequestStatusUpdate(SQLModel):
    status: str  # in_progress | done


# --- Админ ---

class UserRead(SQLModel):
    id: int
    email: str
    role: str
    partner_id: Optional[int]
    author_id: Optional[int]


class UserCreate(SQLModel):
    email: str
    password: str
    role: str  # partner | curator | admin | author
    partner_id: Optional[int] = None  # обязательно для role == "partner"
    author_id: Optional[int] = None  # обязательно для role == "author"


class PartnerCreate(SQLModel):
    name: str
    contact_email: str
