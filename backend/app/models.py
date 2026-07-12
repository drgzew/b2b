from datetime import date, datetime
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


class SubscriptionTag(SQLModel, table=True):
    """Связь многие-ко-многим между подписками и тегами.

    Подписка теперь может объединять несколько тегов в одну "тему"
    (например, "Нефтегаз и цифровизация") — это нужно, чтобы матчинг
    через индекс Жаккара имел смысл (пересечение/объединение множеств тегов).
    """

    subscription_id: Optional[int] = Field(
        default=None, foreign_key="subscription.id", primary_key=True
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
    subscriptions: List["Subscription"] = Relationship(
        back_populates="tags", link_model=SubscriptionTag
    )


class Author(SQLModel, table=True):
    """Профиль автора работы (студента/выпускника).

    Поля соответствуют тому, что реально отдаёт вход через университетскую
    почту: ФИО, фото, дата рождения, направление подготовки. Сейчас профиль
    наполняется через мок-функцию parse_tumgu_profile() в sso.py — см. TODO
    там же про переход на реальный SSO/LDAP ТюмГУ без изменения этой модели.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)  # университетская почта, служит естественным ключом
    full_name: str
    photo_url: Optional[str] = None
    birth_date: Optional[date] = None
    program: Optional[str] = None  # направление подготовки

    # Актуальный статус по трудоустройству — задаётся куратором/админом со слов
    # автора (self-service для авторов вне скоупа пилота, см. docs/api-contract.md).
    job_status: str = Field(default="searching")  # searching | not_searching | employed

    created_at: datetime = Field(default_factory=datetime.utcnow)

    artifacts: List["Artifact"] = Relationship(back_populates="author")


class Artifact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: str  # vkr | article | talk | event
    annotation: str
    file_path: Optional[str] = None

    # Решение куратора по артефакту. Заменяет прежнее поле "status" —
    # теперь это единственный источник правды о том, виден ли артефакт партнёрам:
    # только curator_status == "approved" попадает в дайджест.
    curator_status: str = Field(default="draft")  # draft | approved | rejected

    access_level: str = Field(default="none")  # full | annotation_only | none

    # Было строкой author_name — заменено на связь с полным профилем автора,
    # чтобы профиль можно было открыть по клику (см. GET /authors/{id}).
    author_id: Optional[int] = Field(default=None, foreign_key="author.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # TODO: заменить на pgvector.sqlalchemy.Vector(1536), когда подключим
    # семантический поиск/эмбеддинги (этап "Расширение" в roadmap).
    # Пока оставляем как обычную строку, чтобы не блокировать MVP.
    embedding: Optional[str] = None

    tags: List[Tag] = Relationship(back_populates="artifacts", link_model=ArtifactTag)
    requests: List["Request"] = Relationship(back_populates="artifact")
    author: Optional[Author] = Relationship(back_populates="artifacts")
    internships: List["Internship"] = Relationship(back_populates="artifact")
    favorites: List["Favorite"] = Relationship(back_populates="artifact")


class Partner(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    contact_email: str

    subscriptions: List["Subscription"] = Relationship(back_populates="partner")
    requests: List["Request"] = Relationship(back_populates="partner")
    users: List["User"] = Relationship(back_populates="partner")
    internships: List["Internship"] = Relationship(back_populates="partner")
    favorites: List["Favorite"] = Relationship(back_populates="partner")


class Subscription(SQLModel, table=True):
    """Подписка партнёра на тему — набор из одного или нескольких тегов."""

    id: Optional[int] = Field(default=None, primary_key=True)
    partner_id: int = Field(foreign_key="partner.id")
    name: Optional[str] = None  # человекочитаемое имя темы, например "Нефтегаз и цифровизация"

    partner: Optional[Partner] = Relationship(back_populates="subscriptions")
    tags: List[Tag] = Relationship(back_populates="subscriptions", link_model=SubscriptionTag)
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
    """Запрос партнёра по артефакту: полный текст, стажировка или НИОКР."""

    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_id: int = Field(foreign_key="artifact.id")
    partner_id: int = Field(foreign_key="partner.id")
    type: str  # full_text | internship | rnd
    status: str = Field(default="sent")  # sent | in_progress | done
    created_at: datetime = Field(default_factory=datetime.utcnow)

    artifact: Optional[Artifact] = Relationship(back_populates="requests")
    partner: Optional[Partner] = Relationship(back_populates="requests")


class Internship(SQLModel, table=True):
    """Приглашение партнёра на стажировку по конкретной работе/автору.

    student_name хранится "снимком" на момент приглашения (а не читается
    каждый раз через artifact.author.full_name) — если профиль автора потом
    поменяется или будет удалён, история приглашений останется читаемой.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_id: int = Field(foreign_key="artifact.id")
    partner_id: int = Field(foreign_key="partner.id")
    status: str = Field(default="sent")  # sent | accepted | in_progress | rejected | completed
    student_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    response_date: Optional[datetime] = None

    artifact: Optional[Artifact] = Relationship(back_populates="internships")
    partner: Optional[Partner] = Relationship(back_populates="internships")


class Favorite(SQLModel, table=True):
    """Артефакт, добавленный партнёром в избранное."""

    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_id: int = Field(foreign_key="artifact.id")
    partner_id: int = Field(foreign_key="partner.id")
    added_at: datetime = Field(default_factory=datetime.utcnow)

    artifact: Optional[Artifact] = Relationship(back_populates="favorites")
    partner: Optional[Partner] = Relationship(back_populates="favorites")


class User(SQLModel, table=True):
    """Учётная запись для входа: партнёр или куратор."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: str  # partner | curator | admin
    # Заполнено только для role == "partner": какой компании принадлежит эта учётка
    partner_id: Optional[int] = Field(default=None, foreign_key="partner.id")

    partner: Optional[Partner] = Relationship(back_populates="users")
