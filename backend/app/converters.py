from .models import Artifact
from .schemas import ArtifactRead, TagRead

def to_artifact_read(artifact: Artifact) -> ArtifactRead:
    return ArtifactRead(
        **artifact.dict(exclude={"embedding"}),
        tags=[
            TagRead(
                id=tag.id,
                name=tag.name
            )
            for tag in artifact.tags
        ],
    )
