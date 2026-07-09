from datetime import datetime
from typing import List, Optional

from sqlmodel import SQLModel


class ArtifactCreate(SQLModel):
    title: str
    type: str
    annotation: str
    file_path: Optional[str] = None
    curator_status: str = "draft"
    access_level: str = "none"
    author_name: Optional[str] = None
    tags: List[str] = []  # имена тегов; несуществующие теги будут созданы

class TagRead(SQLModel):
    id: int
    name: str

class ArtifactRead(SQLModel):
    id: int
    title: str
    type: str
    annotation: str
    file_path: Optional[str]
    curator_status: str
    access_level: str
    author_name: Optional[str]
    created_at: datetime
    tags: List[TagRead] = []


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


class ArtifactShortRead(SQLModel):
    id: int
    title: str


class PartnerShortRead(SQLModel):
    id: int
    name: str

class RequestRead(SQLModel):
    id: int
    artifact: ArtifactShortRead
    partner: PartnerShortRead
    type: str
    status: str
    created_at: datetime

# --- Куратор ---

class TagsUpdate(SQLModel):
    tag_ids: List[int]


class RequestStatusUpdate(SQLModel):
    status: str  # in_progress | done
