"""招聘数据分析服务。对应 F4 / T8。"""
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.interview import Interview, InterviewEval
from app.models.job import Job
from app.models.resume import Resume, ResumeMatchResult


def _date_range_filter(query, column, start: date | None, end: date | None):
    if start:
        query = query.filter(column >= start)
    if end:
        # 含 end 当天
        query = query.filter(column < end + timedelta(days=1))
    return query


def _distinct_count(db: Session, column, *filters) -> int:
    """跨方言（PG/SQLite）通用的去重计数，避免使用 PG 专属 DISTINCT ON。"""
    return db.query(func.count(func.distinct(column))).filter(*filters).scalar() or 0


def get_overview(db: Session, start: date | None = None, end: date | None = None) -> dict:
    """招聘周期 / 漏斗转化率 / 渠道效果概览。"""
    resume_q = _date_range_filter(db.query(Resume).filter(Resume.deleted == 0), Resume.created_at, start, end)
    resumes = resume_q.all()
    total_resumes = len(resumes)

    job_q = _date_range_filter(db.query(Job), Job.created_at, start, end)
    total_jobs = job_q.count()

    interview_q = _date_range_filter(db.query(Interview), Interview.created_at, start, end)
    total_interviews = interview_q.count()

    # 漏斗转化率：上传 -> 已评分 -> 已面试 -> 已评价 -> 推荐
    resume_ids = [r.id for r in resumes]
    analyzed_count = _distinct_count(
        db, ResumeMatchResult.resume_id, ResumeMatchResult.resume_id.in_(resume_ids)
    ) if resume_ids else 0
    interviewed_count = _distinct_count(
        db, Interview.resume_id, Interview.resume_id.in_(resume_ids)
    ) if resume_ids else 0
    evaluated_count = (
        db.query(InterviewEval)
        .join(Interview, InterviewEval.interview_id == Interview.id)
        .filter(Interview.resume_id.in_(resume_ids))
        .count()
        if resume_ids
        else 0
    )
    recommended_count = (
        db.query(InterviewEval)
        .join(Interview, InterviewEval.interview_id == Interview.id)
        .filter(Interview.resume_id.in_(resume_ids), InterviewEval.recommendation == "推荐")
        .count()
        if resume_ids
        else 0
    )

    hired_count = (
        db.query(Resume)
        .filter(Resume.id.in_(resume_ids), Resume.status == "hired")
        .count()
        if resume_ids
        else 0
    )

    def _rate(n: int) -> float:
        return round(n / total_resumes, 4) if total_resumes else 0.0

    conversion_rate = {
        "uploaded": total_resumes,
        "analyzed": analyzed_count,
        "analyzed_rate": _rate(analyzed_count),
        "interviewed": interviewed_count,
        "interviewed_rate": _rate(interviewed_count),
        "evaluated": evaluated_count,
        "evaluated_rate": _rate(evaluated_count),
        "recommended": recommended_count,
        "recommended_rate": _rate(recommended_count),
        "hired": hired_count,
        "hired_rate": _rate(hired_count),
    }

    # 招聘周期：简历上传 -> 首次面试评价完成 的平均天数（仅统计已评价的简历）
    cycle_days = _avg_recruitment_cycle_days(db, resume_ids)

    # 渠道效果：按招聘渠道分组的简历量与推荐量/推荐率
    channel_effectiveness = _channel_effectiveness(db, resume_ids)

    return {
        "recruitment_cycle_days": cycle_days,
        "conversion_rate": conversion_rate,
        "channel_effectiveness": channel_effectiveness,
        "total_jobs": total_jobs,
        "total_resumes": total_resumes,
        "total_interviews": total_interviews,
    }


def _avg_recruitment_cycle_days(db: Session, resume_ids: list[int]) -> float | None:
    if not resume_ids:
        return None
    rows = (
        db.query(Resume.created_at, InterviewEval.created_at)
        .join(Interview, Interview.resume_id == Resume.id)
        .join(InterviewEval, InterviewEval.interview_id == Interview.id)
        .filter(Resume.id.in_(resume_ids))
        .all()
    )
    if not rows:
        return None
    deltas = []
    for resume_created, eval_created in rows:
        if resume_created and eval_created:
            deltas.append((eval_created - resume_created).total_seconds() / 86400)
    if not deltas:
        return None
    return round(sum(deltas) / len(deltas), 2)


def _channel_effectiveness(db: Session, resume_ids: list[int]) -> dict:
    """按招聘渠道统计简历量与推荐量/推荐率。对应 PRD F4 渠道效果分析。"""
    if not resume_ids:
        return {}
    upload_rows = (
        db.query(Resume.channel, func.count(Resume.id))
        .filter(Resume.id.in_(resume_ids))
        .group_by(Resume.channel)
        .all()
    )
    recommended_rows = (
        db.query(Resume.channel, func.count(InterviewEval.id))
        .join(Interview, Interview.resume_id == Resume.id)
        .join(InterviewEval, InterviewEval.interview_id == Interview.id)
        .filter(Resume.id.in_(resume_ids), InterviewEval.recommendation == "推荐")
        .group_by(Resume.channel)
        .all()
    )
    recommended_map = dict(recommended_rows)
    result = {}
    for channel, uploaded in upload_rows:
        recommended = recommended_map.get(channel, 0)
        result[channel] = {
            "uploaded": uploaded,
            "recommended": recommended,
            "recommended_rate": round(recommended / uploaded, 4) if uploaded else 0.0,
        }
    return result
