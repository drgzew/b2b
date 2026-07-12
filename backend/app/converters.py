from .models import Artifact
from .schemas import ArtifactRead


def to_artifact_read(artifact: Artifact) -> ArtifactRead:
    return ArtifactRead(
        **artifact.dict(exclude={"embedding", "author_id", "supervisor_id"}),
        tags=[tag.name for tag in artifact.tags],
        author_id=artifact.author_id,
        author_name=artifact.author.full_name if artifact.author else None,
        supervisor_id=artifact.supervisor_id,
        supervisor_name=artifact.supervisor.full_name if artifact.supervisor else None,
    )
