from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class ArtifactTag(SQLModel, table=True):
    """Связь многие-ко-многим между артефактами и тегами."""

    artifact_id: Optional[int] = Field(
        default=None, foreign_key="artifact.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="tag.id", primary_key=True
    )


class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    artifacts: List["Artifact"] = Relationship(
        back_populates="tags", link_model=ArtifactTag
    )
    subscriptions: List["Subscription"] = Relationship(back_populates="tag")


class Artifact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: str  # vkr | article | talk | event
    annotation: str
    file_path: Optional[str] = None
    status: str = Field(default="draft")  # draft | moderation | published
    access_level: str = Field(default="none")  # full | annotation_only | none
    author_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # TODO: заменить на pgvector.sqlalchemy.Vector(1536), когда подключим
    # семантический поиск/эмбеддинги (этап "Расширение" в roadmap).
    # Пока оставляем как обычную строку, чтобы не блокировать MVP.
    embedding: Optional[str] = None

    tags: List[Tag] = Relationship(back_populates="artifacts", link_model=ArtifactTag)
    requests: List["Request"] = Relationship(back_populates="artifact")


class Partner(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    contact_email: str

    subscriptions: List["Subscription"] = Relationship(back_populates="partner")
    requests: List["Request"] = Relationship(back_populates="partner")


class Subscription(SQLModel, table=True):
    """Подписка партнёра на конкретный тег. У партнёра может быть несколько подписок (по одной на тег)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    partner_id: int = Field(foreign_key="partner.id")
    tag_id: int = Field(foreign_key="tag.id")

    partner: Optional[Partner] = Relationship(back_populates="subscriptions")
    tag: Optional[Tag] = Relationship(back_populates="subscriptions")
    digest_items: List["DigestItem"] = Relationship(back_populates="subscription")


class DigestItem(SQLModel, table=True):
    """Артефакт, попавший в дайджест конкретной подписки."""

    id: Optional[int] = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="subscription.id")
    artifact_id: int = Field(foreign_key="artifact.id")
    sent_at: Optional[datetime] = None
    status: str = Field(default="pending")  # pending | sent

    subscription: Optional[Subscription] = Relationship(back_populates="digest_items")


class Request(SQLModel, table=True):
    """Запрос партнёра на полный текст артефакта."""

    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_id: int = Field(foreign_key="artifact.id")
    partner_id: int = Field(foreign_key="partner.id")
    status: str = Field(default="sent")  # sent | with_curator | with_author | approved | declined
    created_at: datetime = Field(default_factory=datetime.utcnow)

    artifact: Optional[Artifact] = Relationship(back_populates="requests")
    partner: Optional[Partner] = Relationship(back_populates="requests")
