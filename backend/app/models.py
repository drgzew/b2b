from datetime import date, datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class ArtifactTag(SQLModel, table=True):
    artifact_id: Optional[int] = Field(default=None, foreign_key="artifact.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class SubscriptionTag(SQLModel, table=True):
    subscription_id: Optional[int] = Field(default=None, foreign_key="subscription.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    artifacts: List["Artifact"] = Relationship(back_populates="tags", link_model=ArtifactTag)
    subscriptions: List["Subscription"] = Relationship(back_populates="tags", link_model=SubscriptionTag)


class Author(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    photo_url: Optional[str] = None
    birth_date: Optional[date] = None
    program: Optional[str] = None
    job_status: str = Field(default="searching")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    artifacts: List["Artifact"] = Relationship(back_populates="author")


class Teacher(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(index=True, unique=True)
    department: str
    position: str
    artifacts: List["Artifact"] = Relationship(back_populates="supervisor")


class Artifact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: str
    annotation: str
    file_path: Optional[str] = None
    curator_status: str = Field(default="draft")
    read_policy: str = Field(default="requires_approval")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    embedding: Optional[str] = None

    author_id: Optional[int] = Field(default=None, foreign_key="author.id")
    supervisor_id: Optional[int] = Field(default=None, foreign_key="teacher.id")

    author: Optional[Author] = Relationship(back_populates="artifacts")
    supervisor: Optional[Teacher] = Relationship(back_populates="artifacts")
    tags: List[Tag] = Relationship(back_populates="artifacts", link_model=ArtifactTag)
    favorites: List["Favorite"] = Relationship(back_populates="artifact")
    internships: List["Internship"] = Relationship(back_populates="artifact")
    requests: List["Request"] = Relationship(back_populates="artifact")
    accesses: List["PartnerArtifactAccess"] = Relationship(back_populates="artifact")


class Partner(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    contact_email: str
    subscriptions: List["Subscription"] = Relationship(back_populates="partner")
    favorites: List["Favorite"] = Relationship(back_populates="partner")
    internships: List["Internship"] = Relationship(back_populates="partner")
    requests: List["Request"] = Relationship(back_populates="partner")
    accesses: List["PartnerArtifactAccess"] = Relationship(back_populates="partner")


class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    partner_id: int = Field(foreign_key="partner.id")
    name: Optional[str] = None
    description: Optional[str] = None
    partner: Optional[Partner] = Relationship(back_populates="subscriptions")
    tags: List[Tag] = Relationship(back_populates="subscriptions", link_model=SubscriptionTag)
    digest_items: List["DigestItem"] = Relationship(back_populates="subscription")


class DigestItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="subscription.id")
    artifact_id: int = Field(foreign_key="artifact.id")
    sent_at: Optional[datetime] = None
    status: str = Field(default="sent")
    subscription: Optional[Subscription] = Relationship(back_populates="digest_items")
    artifact: Optional[Artifact] = Relationship()


class Request(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_id: int = Field(foreign_key="artifact.id")
    partner_id: int = Field(foreign_key="partner.id")
    type: str
    status: str = Field(default="sent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    artifact: Optional[Artifact] = Relationship(back_populates="requests")
    partner: Optional[Partner] = Relationship(back_populates="requests")


class Favorite(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_id: int = Field(foreign_key="artifact.id")
    partner_id: int = Field(foreign_key="partner.id")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    artifact: Optional[Artifact] = Relationship(back_populates="favorites")
    partner: Optional[Partner] = Relationship(back_populates="favorites")


class Internship(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_id: int = Field(foreign_key="artifact.id")
    partner_id: int = Field(foreign_key="partner.id")
    status: str = Field(default="sent")
    student_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    response_date: Optional[datetime] = None
    artifact: Optional[Artifact] = Relationship(back_populates="internships")
    partner: Optional[Partner] = Relationship(back_populates="internships")


class PartnerArtifactAccess(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_id: int = Field(foreign_key="artifact.id")
    partner_id: int = Field(foreign_key="partner.id")
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    artifact: Optional[Artifact] = Relationship(back_populates="accesses")
    partner: Optional[Partner] = Relationship(back_populates="accesses")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: str
    partner_id: Optional[int] = Field(default=None, foreign_key="partner.id")
    author_id: Optional[int] = Field(default=None, foreign_key="author.id")