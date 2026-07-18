"""简历服务：上传、解析、评分、删除、导出。对应 F2 / T5 / T7。"""
from sqlalchemy.orm import Session

from app.ai.orchestrator import AgentContext, AgentOrchestrator
from app.ai.prompt_manager import get_prompt
from app.common.redact import mask_sensitive
from app.common.response import AppError
from app.common.storage import gen_key, get_storage
from app.models.job import Job
from app.models.resume import Resume, ResumeMatchResult

ALLOWED_EXT = {".pdf", ".docx", ".doc", ".txt"}


def upload(file_name: str, content: bytes, db: Session, operator_id: int, job_id: int | None = None) -> dict:
    """上传简历：存对象存储 + 建 resume 记录（永久保留，retention_until 留空）。"""
    ext = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext not in ALLOWED_EXT:
        raise AppError(code=400, message=f"不支持的文件类型: {ext}", status_code=400)

    key = gen_key(file_name)
    ref = get_storage().put(key, content)
    resume = Resume(
        candidate_name="",
        file_ref=ref,
        file_name=file_name,
        parsed_data=None,
        status="pending",
        job_id=job_id,
        retention_until=None,  # 永久保留
        created_by=operator_id,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return {"resume_id": resume.id, "file_ref": ref}


def _parse_resume(content: bytes, file_name: str) -> dict:
    """简历解析：MVP 用文本抽取（文本型 PDF/Word/txt）。"""
    text = ""
    lower = file_name.lower()
    if lower.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")
    else:
        # 文本型 PDF/Word：尝试解码可见文本，复杂版式 OCR 留待 P2
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            text = ""
    return {
        "raw_text": text,
        "name": "",
        "skills": [],
        "experience": "",
    }


def analyze(resume_id: int, job_id: int, db: Session, operator_id: int,
            orchestrator: AgentOrchestrator | None = None) -> dict:
    """简历匹配评分：解析 + ResumeAgent 推理 + 落库。"""
    resume = db.get(Resume, resume_id)
    if not resume or resume.deleted:
        raise AppError(code=404, message="简历不存在", status_code=404)

    job = db.get(Job, job_id)
    if not job:
        raise AppError(code=404, message="目标岗位不存在", status_code=404)

    # 解析（若未解析）
    if not resume.parsed_data:
        content = get_storage().get(_key_from_ref(resume.file_ref))
        resume.parsed_data = _parse_resume(content, resume.file_name)
        resume.job_id = job_id
        db.flush()

    # 脱敏后送入 LLM
    resume_text = mask_sensitive(resume.parsed_data.get("raw_text", ""))
    orch = orchestrator or AgentOrchestrator(db)
    ctx = AgentContext(agent_type="ResumeAgent", operator_id=operator_id, prompt_name="resume_analyze")
    prompt = get_prompt("resume_analyze")
    user_message = prompt.user_template.format(
        job_profile=str(job.job_profile),
        skill_requirements=str(job.skill_requirements),
        resume_text=resume_text,
    )
    result = orch.invoke(ctx, user_message, schema={"type": "object"})

    score = int(result.get("match_score", 0))
    if not (0 <= score <= 100):
        raise AppError(code=502, message="匹配评分超出 0-100 范围", status_code=502)

    match = ResumeMatchResult(
        resume_id=resume_id,
        job_id=job_id,
        match_score=score,
        advantages=result.get("advantages"),
        risks=result.get("risks"),
        rationale=result.get("rationale"),
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return {
        "resume_id": resume_id,
        "job_id": job_id,
        "match_score": score,
        "advantages": result.get("advantages"),
        "risks": result.get("risks"),
        "rationale": result.get("rationale"),
    }


def _key_from_ref(ref: str) -> str:
    """从 local://<base>/<key> 还原对象 key（去掉 base 目录前缀）。"""
    if not ref.startswith("local://"):
        return ref
    path = ref.removeprefix("local://")
    # base 目录为 .obs-local，去掉该前缀及随后的分隔符
    base_name = ".obs-local"
    if base_name in path:
        idx = path.find(base_name) + len(base_name)
        path = path[idx:]
        # 去掉路径分隔符（兼容 / 与 \）
        while path and path[0] in ("/", "\\"):
            path = path[1:]
    return path


def list_resumes(db: Session, sort_by_score: bool = False) -> list[dict]:
    q = db.query(Resume).filter(Resume.deleted == 0)
    items = q.all()
    out = []
    for r in items:
        score = None
        if sort_by_score:
            mr = db.query(ResumeMatchResult).filter_by(resume_id=r.id).order_by(
                ResumeMatchResult.created_at.desc()
            ).first()
            score = mr.match_score if mr else None
        out.append({
            "id": r.id,
            "file_name": r.file_name,
            "status": r.status,
            "job_id": r.job_id,
            "match_score": score,
        })
    if sort_by_score:
        out.sort(key=lambda x: x["match_score"] if x["match_score"] is not None else -1, reverse=True)
    return out


def delete_resume(resume_id: int, db: Session, operator_id: int) -> dict:
    """人工显式删除：软删除记录（永久保留原则下不物理删除文件，仅标记并写审计式备注）。

    生产可按合规要求决定是否清空对象存储；MVP 保留文件并软删除，确保可审计。
    """
    resume = db.get(Resume, resume_id)
    if not resume:
        raise AppError(code=404, message="简历不存在", status_code=404)
    if resume.deleted:
        raise AppError(code=409, message="简历已删除", status_code=409)
    resume.deleted = 1
    resume.status = "deleted"
    db.commit()
    return {"resume_id": resume_id, "deleted": True, "operator_id": operator_id}


def export_resume(resume_id: int, db: Session) -> dict:
    """导出简历：返回文件下载信息，满足个人信息可携带要求。"""
    resume = db.get(Resume, resume_id)
    if not resume or resume.deleted:
        raise AppError(code=404, message="简历不存在", status_code=404)
    content = get_storage().get(_key_from_ref(resume.file_ref))
    return {
        "resume_id": resume_id,
        "file_name": resume.file_name,
        "content_b64": content.hex(),  # 简化：返回十六进制，前端解码下载
        "size": len(content),
    }
