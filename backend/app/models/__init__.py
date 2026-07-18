"""ORM 模型。"""
from app.models.ai_call_log import AiCallLog
from app.models.audit_log import AuditLog
from app.models.dictionary import CompetencyTemplate, PositionTemplate, SkillDict
from app.models.interview import Interview, InterviewEval
from app.models.job import JdVersion, Job
from app.models.resume import Resume, ResumeMatchResult
from app.models.user import User

__all__ = [
    "User",
    "AiCallLog",
    "AuditLog",
    "Job",
    "JdVersion",
    "Resume",
    "ResumeMatchResult",
    "Interview",
    "InterviewEval",
    "PositionTemplate",
    "SkillDict",
    "CompetencyTemplate",
]
