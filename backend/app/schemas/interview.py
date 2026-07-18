"""面试 schema。"""
from pydantic import BaseModel, Field


class InterviewCreateRequest(BaseModel):
    resume_id: int | None = None
    job_id: int | None = None
    record_text: str = Field(..., min_length=1, max_length=20000)


class InterviewEvalResult(BaseModel):
    interview_id: int
    summary: str
    capability_eval: dict
    recommendation: str
    rationale: dict
