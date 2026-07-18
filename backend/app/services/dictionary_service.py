"""字典管理服务：岗位库 / 技能字典 / 能力模板的 CRUD。对应 F5.2 / T9。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import AppError
from app.models.dictionary import CompetencyTemplate, PositionTemplate, SkillDict

# ── 岗位模板 ──────────────────────────────────────────────────────────────────

def create_position_template(req, db: Session, operator_id: int) -> dict:
    pt = PositionTemplate(
        title=req.title, level=req.level,
        job_profile=req.job_profile, skill_requirements=req.skill_requirements,
        created_by=str(operator_id),
    )
    db.add(pt)
    db.commit()
    db.refresh(pt)
    return _pt_to_dict(pt)


def list_position_templates(db: Session) -> list[dict]:
    return [_pt_to_dict(r) for r in db.scalars(select(PositionTemplate).where(PositionTemplate.status == "active"))]


def _pt_to_dict(pt: PositionTemplate) -> dict:
    return {
        "id": pt.id, "title": pt.title, "level": pt.level,
        "job_profile": pt.job_profile, "skill_requirements": pt.skill_requirements,
    }


# ── 技能字典 ──────────────────────────────────────────────────────────────────

def create_skill(req, db: Session) -> dict:
    existing = db.scalar(select(SkillDict).where(SkillDict.name == req.name))
    if existing:
        raise AppError(code=409, message=f"技能词条已存在: {req.name}", status_code=409)
    skill = SkillDict(name=req.name, category=req.category, description=req.description)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return {"id": skill.id, "name": skill.name, "category": skill.category}


def list_skills(db: Session, category: str | None = None) -> list[dict]:
    q = select(SkillDict).where(SkillDict.status == "active")
    if category:
        q = q.where(SkillDict.category == category)
    return [{"id": r.id, "name": r.name, "category": r.category} for r in db.scalars(q)]


# ── 能力维度模板 ───────────────────────────────────────────────────────────────

def create_competency_template(req, db: Session) -> dict:
    ct = CompetencyTemplate(
        name=req.name,
        dimensions={"items": req.dimensions},
        is_default=req.is_default,
    )
    if req.is_default:
        # 确保同时只有一个默认模板
        db.query(CompetencyTemplate).filter(CompetencyTemplate.is_default == True).update({"is_default": False})  # noqa: E712
    db.add(ct)
    db.commit()
    db.refresh(ct)
    return _ct_to_dict(ct)


def get_default_competency_template(db: Session) -> dict | None:
    ct = db.scalar(select(CompetencyTemplate).where(
        CompetencyTemplate.is_default == True, CompetencyTemplate.status == "active"  # noqa: E712
    ))
    return _ct_to_dict(ct) if ct else None


def list_competency_templates(db: Session) -> list[dict]:
    return [_ct_to_dict(r) for r in db.scalars(select(CompetencyTemplate).where(CompetencyTemplate.status == "active"))]


def _ct_to_dict(ct: CompetencyTemplate) -> dict:
    return {
        "id": ct.id, "name": ct.name,
        "dimensions": ct.dimensions.get("items", []) if isinstance(ct.dimensions, dict) else ct.dimensions,
        "is_default": ct.is_default,
    }
