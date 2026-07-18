"""字典管理路由（仅 ADMIN 可写，所有人可读）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.common.response import ok
from app.db import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.dictionary import CompetencyTemplateCreate, PositionTemplateCreate, SkillDictCreate
from app.services import dictionary_service

router = APIRouter(prefix="/dictionary", tags=["dictionary"])

_admin_only = require_roles(Role.ADMIN)


@router.get("/positions")
def list_positions(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    return ok(dictionary_service.list_position_templates(db))


@router.post("/positions")
def create_position(req: PositionTemplateCreate, db: Session = Depends(get_db),
                    user: User = Depends(_admin_only)) -> dict:
    return ok(dictionary_service.create_position_template(req, db, operator_id=user.id))


@router.get("/skills")
def list_skills(category: str | None = None, db: Session = Depends(get_db),
                _: User = Depends(get_current_user)) -> dict:
    return ok(dictionary_service.list_skills(db, category=category))


@router.post("/skills")
def create_skill(req: SkillDictCreate, db: Session = Depends(get_db),
                 _: User = Depends(_admin_only)) -> dict:
    return ok(dictionary_service.create_skill(req, db))


@router.get("/competencies")
def list_competencies(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    return ok(dictionary_service.list_competency_templates(db))


@router.post("/competencies")
def create_competency(req: CompetencyTemplateCreate, db: Session = Depends(get_db),
                      _: User = Depends(_admin_only)) -> dict:
    return ok(dictionary_service.create_competency_template(req, db))


@router.get("/competencies/default")
def get_default_competency(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    return ok(dictionary_service.get_default_competency_template(db))
