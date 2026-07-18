"""简历 schema。"""
from pydantic import BaseModel, Field


class ResumeAnalyzeRequest(BaseModel):
    job_id: int = Field(..., description="目标岗位 ID")


class ResumeAnalyzeResult(BaseModel):
    resume_id: int
    job_id: int
    match_score: int
    advantages: list
    risks: list
    rationale: dict
