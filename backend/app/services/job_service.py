"""岗位与 JD 服务：生成 JD、保存版本。对应 F1 / T4。

JD 生成时可注入 orchestrator（测试用），默认由 AgentOrchestrator 自动 get_llm_client。
由岗位模板库匹配同名等级模板以提升生成质量。
"""
from sqlalchemy.orm import Session

from app.ai.orchestrator import AgentContext, AgentOrchestrator
from app.ai.prompt_manager import get_prompt
from app.common.response import AppError
from app.models.dictionary import PositionTemplate
from app.models.job import JdVersion, Job


def _find_position_template(title: str, level: str, db: Session) -> PositionTemplate | None:
    from sqlalchemy import select

    return db.scalar(
        select(PositionTemplate).where(
            PositionTemplate.title == title,
            PositionTemplate.level == level,
            PositionTemplate.status == "active",
        )
    )


def draft_job(req, db: Session, operator_id: int, orchestrator: AgentOrchestrator | None = None) -> dict:
    orch = orchestrator or AgentOrchestrator(db)
    ctx = AgentContext(agent_type="JobAgent", operator_id=operator_id, prompt_name="job_draft")
    prompt = get_prompt("job_draft")

    business_req = req.business_req
    template = _find_position_template(req.title, req.level, db)
    if template:
        if template.job_profile and not business_req:
            profile_keys = ", ".join(str(k) for k in template.job_profile)
            business_req = f"参考岗位画像关键要素：{profile_keys}"
        if template.skill_requirements:
            skills = template.skill_requirements
            skill_list = skills.get("items", skills) if isinstance(skills, dict) else (skills if isinstance(skills, list) else [])
            if skill_list:
                business_req += f"；建议技能方向：{', '.join(skill_list)}"

    user_message = prompt.user_template.format(
        title=req.title, level=req.level, business_req=business_req
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
    job = db.get(Job, job_id)
    if not job:
        raise AppError(code=404, message="岗位不存在", status_code=404)

    next_no = db.query(JdVersion).filter(JdVersion.job_id == job_id).count() + 1
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
