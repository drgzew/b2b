import os
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .converters import to_artifact_read
from .db import get_session, init_db
from .models import Artifact, Tag
from .routers import admin, auth, authors, curator, partner
from .schemas import ArtifactCreate, ArtifactRead
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Подписка на университет — API")

# Без этого браузер блокирует запросы с фронтенда, если он крутится на другом
# origin (другой домен/порт), даже если бэкенд отвечает 200 — запрос не дойдёт
# до кода ручки, упадёт на preflight OPTIONS. Список origin'ов берём из
# переменной окружения (через запятую), чтобы не хардкодить прод/дев адреса.
# Дефолт покрывает типичные локальные фронтенды (Vite/CRA) для разработки.
_default_origins = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(partner.router)
app.include_router(curator.router)
app.include_router(authors.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/artifacts", response_model=List[ArtifactRead])
def list_artifacts(session: Session = Depends(get_session)):
    artifacts = session.exec(select(Artifact)).all()
    return [to_artifact_read(a) for a in artifacts]


@app.post("/artifacts", response_model=ArtifactRead)
def create_artifact(data: ArtifactCreate, session: Session = Depends(get_session)):
    artifact = Artifact(**data.dict(exclude={"tags"}))

    for tag_name in data.tags:
        tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
        if not tag:
            tag = Tag(name=tag_name)
            session.add(tag)
            session.commit()
            session.refresh(tag)
        artifact.tags.append(tag)

    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return to_artifact_read(artifact)


@app.get("/artifacts/{artifact_id}", response_model=ArtifactRead)
def get_artifact(artifact_id: int, session: Session = Depends(get_session)):
    artifact = session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return to_artifact_read(artifact)
