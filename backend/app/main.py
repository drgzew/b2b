from typing import List

from fastapi import Depends, FastAPI, HTTPException
from .routers import auth, curator
from sqlmodel import Session, select
from fastapi.middleware.cors import CORSMiddleware

from .converters import to_artifact_read
from .db import get_session, init_db
from .models import Artifact, Tag
from .routers import partner
from .schemas import ArtifactCreate, ArtifactRead
from app.routers import tags

app = FastAPI(title="Подписка на университет — API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(partner.router)
app.include_router(curator.router)
app.include_router(tags.router)

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
