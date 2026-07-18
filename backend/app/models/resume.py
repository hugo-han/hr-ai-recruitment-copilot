"""resume 与 resume_match_result 表：简历与匹配评分。对应 system-design 4.2。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base

_json_type = JSONB().with_variant(JSON(), "sqlite")


class Resume(Base):
    __tablename__ = "resume"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    candidate_name: Mapped[str] = mapped_column(String(64), default="")
    file_ref: Mapped[str] = mapped_column(String(512))   # OBS 对象引用（加密文件）
    file_name: Mapped[str] = mapped_column(String(255), default="")
    parsed_data: Mapped[dict | None] = mapped_column(_json_type, nullable=True)  # 结构化解析结果（敏感字段脱敏）
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/interview/hired/rejected
    job_id: Mapped[int | None] = mapped_column(ForeignKey("job.id", ondelete="SET NULL"), index=True)
    # 永久保留：retention_until 默认 NULL（不过期）；删除为人工显式触发
    retention_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    deleted: Mapped[bool] = mapped_column(Integer, default=0)  # 软删除标记（仍保留，符合永久保留+审计）
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ResumeMatchResult(Base):
    __tablename__ = "resume_match_result"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("job.id", ondelete="SET NULL"), index=True)
    match_score: Mapped[int] = mapped_column(Integer)  # 0-100
    advantages: Mapped[dict | None] = mapped_column(_json_type, nullable=True)
    risks: Mapped[dict | None] = mapped_column(_json_type, nullable=True)
    rationale: Mapped[dict | None] = mapped_column(_json_type, nullable=True)  # 命中/缺失项
    ai_call_log_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
