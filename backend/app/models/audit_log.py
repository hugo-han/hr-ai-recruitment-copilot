"""audit_log 表：通用操作审计，只增不删。对应 Issue #2 / TC-705。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base

_json_type = JSONB().with_variant(JSON(), "sqlite")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(32), index=True)       # export / delete / upload / ...
    resource_type: Mapped[str] = mapped_column(String(32), index=True)  # resume / job / interview
    resource_id: Mapped[int] = mapped_column(Integer, index=True)       # 资源主键
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    detail: Mapped[dict | None] = mapped_column(_json_type, nullable=True)  # 补充信息
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
