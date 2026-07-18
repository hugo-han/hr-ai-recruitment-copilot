"""字典管理 schema。"""
from pydantic import BaseModel, Field


class PositionTemplateCreate(BaseModel):
    title: str = Field(..., max_length=128)
    level: str = Field(..., max_length=32)
    job_profile: dict | None = None
    skill_requirements: dict | None = None


class SkillDictCreate(BaseModel):
    name: str = Field(..., max_length=64)
    category: str = Field("general", max_length=32)
    description: str | None = None


class CompetencyTemplateCreate(BaseModel):
    name: str = Field(..., max_length=64)
    dimensions: list[dict]  # [{"name": "专业技能", "description": "..."}]
    is_default: bool = False
