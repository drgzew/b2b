from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ..db import get_session
from ..models import Tag
from ..schemas import TagRead

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("", response_model=List[TagRead])
def list_tags(session: Session = Depends(get_session),):
    return session.exec(select(Tag)).all()