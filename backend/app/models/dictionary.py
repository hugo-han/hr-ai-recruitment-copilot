"""字典表：岗位模板、技能字典、能力维度模板。对应 system-design 4.2 dictionary + F5.2。"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base

_json_type = JSONB().with_variant(JSON(), "sqlite")


class PositionTemplate(Base):
    """岗位模板库：标准化岗位画像，供 JD 生成参考。"""

    __tablename__ = "position_template"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), index=True)
    level: Mapped[str] = mapped_column(String(32))
    job_profile: Mapped[dict | None] = mapped_column(_json_type, nullable=True)
    skill_requirements: Mapped[dict | None] = mapped_column(_json_type, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_by: Mapped[int | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SkillDict(Base):
    """技能字典：标准化技能词条。"""

    __tablename__ = "skill_dict"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(32), default="general")  # backend/frontend/general/…
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CompetencyTemplate(Base):
    """能力维度模板：面试评价标准，对应 InterviewAgent 使用的 COMPETENCY_TEMPLATE。"""

    __tablename__ = "competency_template"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    dimensions: Mapped[dict] = mapped_column(_json_type)  # [{"name": "专业技能", "description": "..."}]
    is_default: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
