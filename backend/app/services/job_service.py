"""岗位与 JD 服务：生成 JD、保存版本。对应 F1 / T4。"""
from sqlalchemy.orm import Session

from app.ai.orchestrator import AgentContext, AgentOrchestrator
from app.ai.prompt_manager import get_prompt
from app.models.job import JdVersion, Job


def draft_job(req, db: Session, operator_id: int, orchestrator: AgentOrchestrator | None = None) -> dict:
    """AI 生成 JD：创建 job + 落 jd_version(source=AI) + 写审计。"""
    orch = orchestrator or AgentOrchestrator(db)
    ctx = AgentContext(agent_type="JobAgent", operator_id=operator_id, prompt_name="job_draft")
    prompt = get_prompt("job_draft")
    user_message = prompt.user_template.format(
        title=req.title, level=req.level, business_req=req.business_req
    )

    result = orch.invoke(ctx, user_message, schema={"type": "object"})

    job = Job(
        title=req.title,
        level=req.level,
        business_req=req.business_req,
        job_profile=result.get("job_profile"),
        skill_requirements=result.get("skill_requirements"),
        status="draft",
        created_by=operator_id,
    )
    db.add(job)
    db.flush()

    version = JdVersion(
        job_id=job.id,
        version_no=1,
        content={"jd": result.get("jd"), "job_profile": result.get("job_profile"),
                  "skill_requirements": result.get("skill_requirements")},
        source="AI",
        created_by=operator_id,
    )
    db.add(version)
    db.commit()
    db.refresh(job)
    db.refresh(version)

    return {
        "job_id": job.id,
        "version_no": version.version_no,
        "jd": result.get("jd"),
        "job_profile": result.get("job_profile"),
        "skill_requirements": result.get("skill_requirements"),
        "rationale": result.get("rationale"),
    }


def save_human_version(job_id: int, req, db: Session, operator_id: int) -> dict:
    """人工编辑后保存为新版本（source=HUMAN）。"""
    job = db.get(Job, job_id)
    if not job:
        from app.common.response import AppError

        raise AppError(code=404, message="岗位不存在", status_code=404)

    next_no = (
        db.query(JdVersion).filter(JdVersion.job_id == job_id).count() + 1
    )
    version = JdVersion(
        job_id=job_id,
        version_no=next_no,
        content={
            "jd": req.jd,
            "job_profile": req.job_profile or job.job_profile,
            "skill_requirements": req.skill_requirements if req.skill_requirements is not None else job.skill_requirements,
        },
        source="HUMAN",
        created_by=operator_id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return {"job_id": job_id, "version_no": version.version_no, "source": "HUMAN"}


def list_versions(job_id: int, db: Session) -> list[dict]:
    rows = db.query(JdVersion).filter(JdVersion.job_id == job_id).order_by(JdVersion.version_no).all()
    return [
        {"version_no": r.version_no, "source": r.source, "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]


def get_job(job_id: int, db: Session) -> dict | None:
    job = db.get(Job, job_id)
    if not job:
        return None
    return {
        "id": job.id,
        "title": job.title,
        "level": job.level,
        "business_req": job.business_req,
        "job_profile": job.job_profile,
        "skill_requirements": job.skill_requirements,
        "status": job.status,
    }
