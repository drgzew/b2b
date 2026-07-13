from sqlmodel import Session, select

from .models import Artifact, PartnerArtifactAccess


def has_read_access(session: Session, artifact: Artifact, partner_id: int) -> bool:
    """Может ли конкретный партнёр читать полный текст артефакта прямо сейчас.
    Два независимых пути к True:
    1. Автор поставил read_policy = "open" — открыто всем партнёрам без запроса.
    2. Есть отдельное разрешение именно для этого партнёра (PartnerArtifactAccess),
       выданное после одобрения запроса автором/куратором.
    По умолчанию (read_policy = "requires_approval" и разрешения нет) — False,
    это и есть тот самый "запрет по умолчанию" из требований.
    """
    if artifact.read_policy == "open":
        return True

    grant = session.exec(
        select(PartnerArtifactAccess).where(
            PartnerArtifactAccess.artifact_id == artifact.id,
            PartnerArtifactAccess.partner_id == partner_id,
        )
    ).first()
    return grant is not None


def grant_read_access(session: Session, artifact_id: int, partner_id: int) -> None:
    """Выдаёт партнёру доступ к конкретному артефакту.
    Идемпотентно — повторное одобрение (например, и куратором, и автором) не создаёт дубль.
    """
    existing = session.exec(
        select(PartnerArtifactAccess).where(
            PartnerArtifactAccess.artifact_id == artifact_id,
            PartnerArtifactAccess.partner_id == partner_id,
        )
    ).first()
    if existing:
        return

    session.add(PartnerArtifactAccess(artifact_id=artifact_id, partner_id=partner_id))
    session.commit()