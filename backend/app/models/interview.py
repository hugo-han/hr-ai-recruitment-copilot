"""interview 与 interview_eval 表：面试记录与评价。对应 system-design 4.2。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base

_json_type = JSONB().with_variant(JSON(), "sqlite")

# 统一能力维度模板（MVP 内置，P1 落库管理）
COMPETENCY_TEMPLATE = ["专业技能", "沟通表达", "解决问题", "团队协作", "学习能力"]


class Interview(Base):
    __tablename__ = "interview"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resume.id", ondelete="SET NULL"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("job.id", ondelete="SET NULL"), index=True)
    record_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="recorded")  # recorded/evaluated
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class InterviewEval(Base):
    __tablename__ = "interview_eval"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interview.id", ondelete="CASCADE"), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    capability_eval: Mapped[dict | None] = mapped_column(_json_type, nullable=True)
    recommendation: Mapped[str] = mapped_column(String(16))  # 推荐/待定/不推荐
    rationale: Mapped[dict | None] = mapped_column(_json_type, nullable=True)
    ai_call_log_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
