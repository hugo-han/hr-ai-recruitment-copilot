"""鉴权依赖：JWT 解析与角色控制。对应 PRD F5.1。"""
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.common.response import AppError
from app.common.security import decode_token
from app.db import get_db
from app.models.enums import ROLE_PERMISSIONS, Role
from app.models.user import User


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    """从 Bearer token 解析当前用户。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(code=401, message="未提供认证令牌", status_code=401)
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise AppError(code=401, message="令牌类型错误", status_code=401)
    user_id = int(payload.get("sub", "0"))
    user = db.get(User, user_id)
    if not user or user.status != "active":
        raise AppError(code=401, message="用户不存在或已禁用", status_code=401)
    return user


def require_roles(*roles: Role):
    """角色门禁依赖工厂：仅允许指定角色访问。"""

    def _checker(user: User = Depends(get_current_user)) -> User:
        user_role = Role(user.role.value) if isinstance(user.role, Role) else Role(user.role)
        if user_role not in roles:
            raise AppError(code=403, message="无权限访问该资源", status_code=403)
        return user

    return _checker


def require_scope(scope: str):
    """功能域门禁依赖工厂：基于 ROLE_PERMISSIONS 控制功能可见性。"""

    def _checker(user: User = Depends(get_current_user)) -> User:
        user_role = Role(user.role.value) if isinstance(user.role, Role) else Role(user.role)
        allowed = ROLE_PERMISSIONS.get(user_role, set())
        if scope not in allowed:
            raise AppError(code=403, message="无权限访问该功能", status_code=403)
        return user

    return _checker
