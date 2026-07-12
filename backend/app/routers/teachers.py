from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Teacher, User
from ..schemas import TeacherRead
from ..security import require_role

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=List[TeacherRead])
def list_teachers(
    user: User = Depends(require_role("curator", "admin")),
    session: Session = Depends(get_session),
):
    teachers = session.exec(select(Teacher)).all()
    return [TeacherRead(**t.dict()) for t in teachers]


@router.get("/{teacher_id}", response_model=TeacherRead)
def get_teacher(
    teacher_id: int,
    # Тот же набор ролей, что и у GET /authors/{id} — кликабельный профиль
    # доступен из карточки артефакта партнёру, куратору и админу.
    user: User = Depends(require_role("curator", "admin", "partner")),
    session: Session = Depends(get_session),
):
    teacher = session.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return TeacherRead(**teacher.dict())
