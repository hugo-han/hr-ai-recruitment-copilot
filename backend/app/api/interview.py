"""面试路由。对应 F3 / T6。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.common.response import ok
from app.db import get_db
from app.models.user import User
from app.schemas.interview import InterviewCreateRequest
from app.services import interview_service

router = APIRouter(prefix="/interviews", tags=["interview"])


@router.post("")
def create(req: InterviewCreateRequest, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)) -> dict:
    return ok(interview_service.create_record(req, db, operator_id=user.id))


@router.post("/{interview_id}/evaluate")
def evaluate(interview_id: int, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)) -> dict:
    return ok(interview_service.evaluate(interview_id, db, operator_id=user.id))
