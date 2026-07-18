"""任务包。"""
from app.tasks.resume_tasks import analyze_resume_task, batch_analyze_resumes

__all__ = ["analyze_resume_task", "batch_analyze_resumes"]
