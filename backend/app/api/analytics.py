"""招聘数据分析路由。对应 F4 / T8。"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.auth import require_scope
from app.common.response import ok
from app.db import get_db
from app.models.user import User
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_scope("analytics")),
) -> dict:
    """招聘周期 / 漏斗转化率 / 渠道效果概览。仅 HR_LEAD / ADMIN 可访问。"""
    return ok(analytics_service.get_overview(db, start=start, end=end))
