from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from .db import get_session, init_db
from .models import Artifact, Tag
from .schemas import ArtifactCreate, ArtifactRead

app = FastAPI(title="Подписка на университет — API")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


def _to_read_model(artifact: Artifact) -> ArtifactRead:
    return ArtifactRead(
        **artifact.dict(exclude={"embedding"}),
        tags=[tag.name for tag in artifact.tags],
    )


@app.get("/artifacts", response_model=List[ArtifactRead])
def list_artifacts(session: Session = Depends(get_session)):
    artifacts = session.exec(select(Artifact)).all()
    return [_to_read_model(a) for a in artifacts]


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
    return _to_read_model(artifact)


@app.get("/artifacts/{artifact_id}", response_model=ArtifactRead)
def get_artifact(artifact_id: int, session: Session = Depends(get_session)):
    artifact = session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _to_read_model(artifact)
