from .models import Artifact
from .schemas import ArtifactRead


def to_artifact_read(artifact: Artifact) -> ArtifactRead:
    return ArtifactRead(
        **artifact.dict(exclude={"embedding"}),
        tags=[tag.name for tag in artifact.tags],
    )
