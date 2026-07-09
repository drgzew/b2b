import os
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://app:app@localhost:5432/app",
)

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """Создаёт таблицы по описанным SQLModel-моделям, если их ещё нет."""
    # Импорт внутри функции, чтобы модели точно успели зарегистрироваться в metadata
    from . import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
