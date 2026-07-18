"""岗位与 JD 相关 schema。"""
from pydantic import BaseModel, Field


class JobDraftRequest(BaseModel):
    """AI 生成 JD 入参。对应 F1.1~F1.4。"""
    title: str = Field(..., min_length=1, max_length=128, description="岗位名称")
    level: str = Field(..., min_length=1, max_length=32, description="岗位等级")
    business_req: str = Field("", max_length=4000, description="业务要求")


class JobDraftResult(BaseModel):
    job_id: int
    version_no: int
    jd: dict
    job_profile: dict
    skill_requirements: list
    rationale: str


class JobUpdateRequest(BaseModel):
    """人工编辑 JD 后保存为新版本。"""
    jd: dict
    job_profile: dict | None = None
    skill_requirements: list | None = None
