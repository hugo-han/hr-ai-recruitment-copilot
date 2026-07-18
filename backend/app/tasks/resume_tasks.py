"""异步任务：批量简历评分。

每份简历独立一个 Task，互不阻塞。
测试时 task_always_eager=True，任务同步执行，无需 broker。
"""
from app.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def analyze_resume_task(self, resume_id: int, job_id: int, operator_id: int) -> dict:
    """分析单份简历（可独立重试）。"""
    import app.db as _db  # 通过模块引用获取 SessionLocal，便于测试打 patch
    from app.services.resume_service import analyze

    db = _db.SessionLocal()
    try:
        return analyze(resume_id, job_id, db, operator_id)
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc) from exc
    finally:
        db.close()


def batch_analyze_resumes(resume_ids: list[int], job_id: int, operator_id: int) -> dict:
    """批量提交：为每份简历派发异步 Task，立即返回 task_ids 供前端轮询。"""
    task_ids = []
    for rid in resume_ids:
        result = analyze_resume_task.delay(rid, job_id, operator_id)
        task_ids.append({"resume_id": rid, "task_id": result.id})
    return {"submitted": len(task_ids), "tasks": task_ids}
