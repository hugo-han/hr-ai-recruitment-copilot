"""user 表：用户与角色。对应 PRD F5.1。"""
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import Role


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # bcrypt，禁止明文
    name: Mapped[str] = mapped_column(String(64))
    role: Mapped[Role] = mapped_column(String(32), default=Role.HR)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active/disabled

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
