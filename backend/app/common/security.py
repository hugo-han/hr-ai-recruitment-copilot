"""安全工具：密码哈希与 JWT 签发/校验。

使用 bcrypt 4.x 直接 API（passlib 与 bcrypt>=4.1 存在兼容性问题）。
"""
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.common.response import AppError
from app.config import settings


def hash_password(raw: str) -> str:
    # bcrypt 要求密码为 bytes，最大长度 72 字节
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


ALGORITHM = settings.jwt_algorithm


def _create_token(subject: str | int, extra: dict[str, Any] | None, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(subject), "iat": now, "exp": now + expires_delta}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.app_secret_key, algorithm=ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(
        user_id,
        {"role": role, "type": "access"},
        timedelta(minutes=settings.jwt_access_expire_minutes),
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id,
        {"type": "refresh"},
        timedelta(days=settings.jwt_refresh_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.app_secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise AppError(code=401, message="无效或过期的令牌", status_code=401) from exc
