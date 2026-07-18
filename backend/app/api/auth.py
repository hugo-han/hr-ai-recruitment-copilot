"""认证路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.common.response import ok
from app.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)) -> dict:
    return ok(auth_service.login(req, db))


@router.post("/refresh")
def refresh(req: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    return ok(auth_service.refresh(req.refresh_token, db))


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    """返回当前登录用户信息，用于前端校验 token。"""
    return ok(
        {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        }
    )

