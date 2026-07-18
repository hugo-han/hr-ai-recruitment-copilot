"""岗位与 JD 路由。对应 F1 / T4。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.common.response import ok
from app.db import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.job import JobDraftRequest, JobUpdateRequest
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["job"])


@router.post("/draft")
def draft(req: JobDraftRequest, db: Session = Depends(get_db),
          user: User = Depends(require_roles(Role.HR, Role.HR_LEAD, Role.ADMIN))) -> dict:
    """AI 生成 JD / 岗位画像 / 技能要求。"""
    return ok(job_service.draft_job(req, db, operator_id=user.id))


@router.get("/{job_id}")
def detail(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    from app.common.response import AppError

    data = job_service.get_job(job_id, db)
    if not data:
        raise AppError(code=404, message="岗位不存在", status_code=404)
    return ok(data)


@router.put("/{job_id}")
def update(job_id: int, req: JobUpdateRequest, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)) -> dict:
    """人工编辑 JD 并保存为新版本。"""
    return ok(job_service.save_human_version(job_id, req, db, operator_id=user.id))


@router.get("/{job_id}/versions")
def versions(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return ok(job_service.list_versions(job_id, db))
