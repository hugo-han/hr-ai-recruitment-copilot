"""job 与 jd_version 表：岗位与 JD 版本。对应 system-design 4.2。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base

# PG 用 JSONB，SQLite 退化用 JSON（测试兼容）
_json_type = JSONB().with_variant(JSON(), "sqlite")


class Job(Base):
    __tablename__ = "job"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128))
    level: Mapped[str] = mapped_column(String(32))
    business_req: Mapped[str] = mapped_column(Text, default="")
    job_profile: Mapped[dict | None] = mapped_column(_json_type, nullable=True)
    skill_requirements: Mapped[dict | None] = mapped_column(_json_type, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft/published/closed
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class JdVersion(Base):
    __tablename__ = "jd_version"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[dict] = mapped_column(_json_type)   # JD 完整内容
    source: Mapped[str] = mapped_column(String(16))     # AI / HUMAN
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
