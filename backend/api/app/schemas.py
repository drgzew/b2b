from datetime import datetime
from typing import List, Optional

from sqlmodel import SQLModel


class ArtifactCreate(SQLModel):
    title: str
    type: str
    annotation: str
    file_path: Optional[str] = None
    status: str = "draft"
    access_level: str = "none"
    author_name: Optional[str] = None
    tags: List[str] = []  # имена тегов; несуществующие теги будут созданы


class ArtifactRead(SQLModel):
    id: int
    title: str
    type: str
    annotation: str
    file_path: Optional[str]
    status: str
    access_level: str
    author_name: Optional[str]
    created_at: datetime
    tags: List[str] = []
