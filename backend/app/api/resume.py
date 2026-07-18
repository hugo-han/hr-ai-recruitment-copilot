"""简历路由。对应 F2 / T5 / T7。"""
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.common.response import ok
from app.db import get_db
from app.models.user import User
from app.schemas.resume import ResumeAnalyzeRequest
from app.services import resume_service

router = APIRouter(prefix="/resumes", tags=["resume"])


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    job_id: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    content = await file.read()
    return ok(resume_service.upload(file.filename or "resume", content, db, operator_id=user.id, job_id=job_id))


@router.post("/{resume_id}/analyze")
def analyze(resume_id: int, req: ResumeAnalyzeRequest, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)) -> dict:
    return ok(resume_service.analyze(resume_id, req.job_id, db, operator_id=user.id))


@router.get("")
def list_(sort: str | None = None, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)) -> dict:
    return ok(resume_service.list_resumes(db, sort_by_score=(sort == "score")))


@router.delete("/{resume_id}")
def delete(resume_id: int, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)) -> dict:
    return ok(resume_service.delete_resume(resume_id, db, operator_id=user.id))


@router.get("/{resume_id}/export")
def export(resume_id: int, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)) -> dict:
    return ok(resume_service.export_resume(resume_id, db))
