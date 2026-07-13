# backend/app/db.py
from typing import Generator
import os

from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# For sqlite need check_same_thread
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db() -> None:
    # импортируем models здесь, чтобы таблицы были известны
    from . import models  # noqa: F401

    SQLModel.metadata.create_all(engine)