from .models import Artifact
from .schemas import ArtifactRead, TagRead


def to_artifact_read(artifact: Artifact) -> ArtifactRead:
    return ArtifactRead(
        id=artifact.id,
        title=artifact.title,
        type=artifact.type,
        annotation=artifact.annotation,
        file_path=artifact.file_path,
        curator_status=artifact.curator_status,
        read_policy=artifact.read_policy,
        created_at=artifact.created_at,
        tags=[TagRead(id=tag.id, name=tag.name) for tag in artifact.tags],
        author_id=artifact.author_id,
        author_name=artifact.author.full_name if artifact.author else None,
        supervisor_id=artifact.supervisor_id,
        supervisor_name=artifact.supervisor.full_name if artifact.supervisor else None,
    )