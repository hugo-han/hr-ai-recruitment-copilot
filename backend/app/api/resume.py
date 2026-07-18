"""简历路由。对应 F2 / T5 / T7 / T9 / F5.3。"""
from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.common.response import ok
from app.db import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.resume import ResumeAnalyzeRequest
from app.services import resume_service

router = APIRouter(prefix="/resumes", tags=["resume"])


class BatchAnalyzeRequest(BaseModel):
    resume_ids: list[int]
    job_id: int


class TransitionRequest(BaseModel):
    target_status: str


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    job_id: int | None = Form(None),
    channel: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.HR, Role.HR_LEAD, Role.ADMIN)),
) -> dict:
    content = await file.read()
    return ok(
        resume_service.upload(
            file.filename or "resume", content, db, operator_id=user.id, job_id=job_id, channel=channel
        )
    )


@router.post("/{resume_id}/analyze")
def analyze(resume_id: int, req: ResumeAnalyzeRequest, db: Session = Depends(get_db),
            user: User = Depends(require_roles(Role.HR, Role.HR_LEAD, Role.ADMIN))) -> dict:
    return ok(resume_service.analyze(resume_id, req.job_id, db, operator_id=user.id))


@router.get("")
def list_(sort: str | None = None, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)) -> dict:
    return ok(resume_service.list_resumes(db, sort_by_score=(sort == "score")))


@router.delete("/{resume_id}")
def delete(resume_id: int, db: Session = Depends(get_db),
           user: User = Depends(require_roles(Role.HR_LEAD, Role.ADMIN))) -> dict:
    return ok(resume_service.delete_resume(resume_id, db, operator_id=user.id))


@router.get("/{resume_id}/export")
def export(resume_id: int, db: Session = Depends(get_db),
           user: User = Depends(require_roles(Role.HR_LEAD, Role.ADMIN))) -> dict:
    return ok(resume_service.export_resume(resume_id, db))


@router.post("/batch-analyze")
def batch_analyze(req: BatchAnalyzeRequest,
                  user: User = Depends(require_roles(Role.HR, Role.HR_LEAD, Role.ADMIN))) -> dict:
    """批量异步评分：派发 Celery Task，立即返回 task_ids 供轮询。"""
    from app.tasks.resume_tasks import batch_analyze_resumes

    return ok(batch_analyze_resumes(req.resume_ids, req.job_id, operator_id=user.id))


@router.get("/tasks/{task_id}")
def task_status(task_id: str, _: User = Depends(get_current_user)) -> dict:
    """查询异步任务状态（Celery AsyncResult）。"""
    from celery.result import AsyncResult

    from app.celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)
    return ok({
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    })


@router.put("/{resume_id}/status")
def transition(resume_id: int, req: TransitionRequest, db: Session = Depends(get_db),
               user: User = Depends(require_roles(Role.HR, Role.HR_LEAD, Role.ADMIN))) -> dict:
    """候选人状态流转：pending → interview → hired / rejected。对应 F5.3 / US-07。"""
    return ok(resume_service.transition_status(resume_id, req.target_status, db, operator_id=user.id))
