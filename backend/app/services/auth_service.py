"""认证服务：登录、刷新令牌。对应 PRD F5.1。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import AppError
from app.common.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.enums import Role
from app.models.user import User
from app.schemas.auth import LoginRequest


def _role_value(role: Role | str) -> str:
    return role.value if isinstance(role, Role) else str(role)


def login(req: LoginRequest, db: Session) -> dict:
    user = db.scalar(select(User).where(User.username == req.username))
    if not user or not verify_password(req.password, user.password_hash):
        raise AppError(code=401, message="用户名或密码错误", status_code=401)
    if user.status != "active":
        raise AppError(code=403, message="用户已禁用", status_code=403)
    return {
        "access_token": create_access_token(user.id, _role_value(user.role)),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
        "role": _role_value(user.role),
        "name": user.name,
    }


def refresh(refresh_token: str, db: Session) -> dict:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise AppError(code=401, message="非刷新令牌", status_code=401)
    user_id = int(payload.get("sub", "0"))
    user = db.get(User, user_id)
    if not user or user.status != "active":
        raise AppError(code=401, message="用户不存在或已禁用", status_code=401)
    return {
        "access_token": create_access_token(user.id, _role_value(user.role)),
        "token_type": "bearer",
        "role": _role_value(user.role),
    }
