"""面试服务：录入记录、生成评价。对应 F3 / T6。"""
from sqlalchemy.orm import Session

from app.ai.orchestrator import AgentContext, AgentOrchestrator
from app.ai.prompt_manager import get_prompt
from app.common.response import AppError
from app.models.interview import COMPETENCY_TEMPLATE, Interview, InterviewEval

VALID_RECOMMENDATIONS = {"推荐", "待定", "不推荐"}


def create_record(req, db: Session, operator_id: int) -> dict:
    interview = Interview(
        resume_id=req.resume_id,
        job_id=req.job_id,
        record_text=req.record_text,
        status="recorded",
        created_by=operator_id,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return {"interview_id": interview.id, "status": interview.status}


def evaluate(interview_id: int, db: Session, operator_id: int,
             orchestrator: AgentOrchestrator | None = None) -> dict:
    interview = db.get(Interview, interview_id)
    if not interview:
        raise AppError(code=404, message="面试记录不存在", status_code=404)

    orch = orchestrator or AgentOrchestrator(db)
    ctx = AgentContext(agent_type="InterviewAgent", operator_id=operator_id, prompt_name="interview_eval")
    prompt = get_prompt("interview_eval")
    user_message = prompt.user_template.format(
        competency_template=",".join(COMPETENCY_TEMPLATE),
        record_text=interview.record_text,
    )
    result = orch.invoke(ctx, user_message, schema={"type": "object"})

    recommendation = result.get("recommendation", "")
    if recommendation not in VALID_RECOMMENDATIONS:
        raise AppError(code=502, message=f"推荐建议非法：{recommendation}", status_code=502)

    # 校验能力维度覆盖
    cap_eval = result.get("capability_eval") or {}
    if isinstance(cap_eval, dict) and cap_eval:
        missing_dims = [d for d in COMPETENCY_TEMPLATE if d not in cap_eval]
        if missing_dims:
            raise AppError(code=502, message=f"能力评价缺少维度：{missing_dims}", status_code=502)

    ev = InterviewEval(
        interview_id=interview_id,
        summary=result.get("summary", ""),
        capability_eval=cap_eval,
        recommendation=recommendation,
        rationale=result.get("rationale"),
    )
    db.add(ev)
    interview.status = "evaluated"
    db.commit()
    db.refresh(ev)
    return {
        "interview_id": interview_id,
        "summary": ev.summary,
        "capability_eval": ev.capability_eval,
        "recommendation": ev.recommendation,
        "rationale": ev.rationale,
    }
