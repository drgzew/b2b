from datetime import date, datetime
from typing import List, Optional
from sqlmodel import SQLModel


# --- Автор ---
class AuthorRead(SQLModel):
    id: int
    email: Optional[str]
    full_name: str
    photo_url: Optional[str]
    birth_date: Optional[date]
    program: Optional[str]
    job_status: str


class AuthorPublicRead(SQLModel):
    id: int
    full_name: str
    photo_url: Optional[str]
    program: Optional[str]
    job_status: str


class AuthorJobStatusUpdate(SQLModel):
    job_status: str


# --- Импорт артефактов (без консоли, см. POST /admin/import) ---
class ImportResult(SQLModel):
    total: int
    imported: int
    skipped: int
    errors: int
    error_details: List[str]
    tags_created: int
    tags_existing: int
    with_annotation: int
    with_tags: int


class TumguSsoLogin(SQLModel):
    email: str


class TeacherRead(SQLModel):
    id: int
    full_name: str
    email: str
    department: str
    position: str


# --- Артефакт ---
class TagRead(SQLModel):
    id: int
    name: str


class ArtifactCreate(SQLModel):
    title: str
    type: str
    annotation: str
    file_path: Optional[str] = None
    curator_status: str = "draft"
    read_policy: str = "requires_approval"
    author_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    tags: List[str] = []


class ArtifactRead(SQLModel):
    id: int
    title: str
    type: str
    annotation: str
    file_path: Optional[str]
    curator_status: str
    read_policy: str
    created_at: datetime
    tags: List[TagRead] = []
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    supervisor_id: Optional[int] = None
    supervisor_name: Optional[str] = None


class ReadPolicyUpdate(SQLModel):
    read_policy: str


class ReadAccessResponse(SQLModel):
    mode: str
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
    description: Optional[str] = None


class SubscriptionTopic(SQLModel):
    name: str
    tags: List[str]
    description: Optional[str] = None


class SubscriptionUpdate(SQLModel):
    subscriptions: List[SubscriptionTopic]


class DigestEntry(SQLModel):
    artifact: ArtifactRead
    relevance: float
    can_read: bool = False


class RequestCreate(SQLModel):
    artifact_id: int
    type: str


class FavoriteCreate(SQLModel):
    artifact_id: int


class FavoriteRead(SQLModel):
    id: int
    artifact_id: int
    partner_id: int
    added_at: datetime
    artifact: ArtifactRead


class InternshipCreate(SQLModel):
    artifact_id: int
    student_name: str


class InternshipStatusUpdate(SQLModel):
    status: str


class InternshipRead(SQLModel):
    id: int
    artifact_id: int
    partner_id: int
    status: str
    student_name: str
    created_at: datetime
    response_date: Optional[datetime]
    artifact_title: Optional[str] = None
    artifact: Optional[ArtifactRead] = None


# --- Куратор ---
class TagsUpdate(SQLModel):
    tag_ids: List[int]


class RequestStatusUpdate(SQLModel):
    status: str


class RequestDecision(SQLModel):
    approve: bool


class AuthorRequestRead(SQLModel):
    id: int
    artifact_id: int
    artifact_title: str
    partner_id: int
    partner_name: str
    type: str
    status: str
    created_at: datetime


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
    role: str
    partner_id: Optional[int] = None
    author_id: Optional[int] = None


class PartnerCreate(SQLModel):
    name: str
    contact_email: str

class ArtifactShortRead(SQLModel):
    id: int
    title: str
    author_name: str | None = None


class PartnerShortRead(SQLModel):
    id: int
    name: str

class RequestRead(SQLModel):
    id: int

    artifact_id: int
    partner_id: int

    artifact: ArtifactShortRead
    partner: PartnerShortRead

    type: str
    status: str
    created_at: datetime