"""字典管理与批量异步评分测试。覆盖 T9。"""
import pytest

from app.ai.llm_client import MockClient
from app.ai.orchestrator import AgentOrchestrator
from app.common.response import AppError
from app.common.security import hash_password
from app.models.enums import Role
from app.models.job import Job
from app.models.resume import ResumeMatchResult
from app.models.user import User
from app.schemas.dictionary import CompetencyTemplateCreate, PositionTemplateCreate, SkillDictCreate
from app.schemas.job import JobDraftRequest
from app.services import dictionary_service, job_service, resume_service

# ── 字典管理 ──────────────────────────────────────────────────────────────────


def _seed_admin(db):
    db.add(User(username="admin_t9", password_hash=hash_password("x"), name="admin", role=Role.ADMIN))
    db.commit()
    return db.query(User).filter_by(username="admin_t9").first()


def _job_orch(db):
    return AgentOrchestrator(db, client=MockClient().with_response(
        "岗位",
        {"jd": {"title": "Java工程师"}, "job_profile": {"方向": "后端"},
         "skill_requirements": ["Java"], "rationale": "依据岗位"},
    ))


def _resume_orch(db, score=80):
    return AgentOrchestrator(db, client=MockClient().with_response(
        "简历",
        {"match_score": score, "advantages": ["扎实"], "risks": [], "rationale": {"hit": ["Java"]}},
    ))


def test_create_position_template(db_session):
    admin = _seed_admin(db_session)
    req = PositionTemplateCreate(title="Java工程师", level="P5",
                                  job_profile={"方向": "后端"}, skill_requirements={"items": ["Java"]})
    result = dictionary_service.create_position_template(req, db_session, operator_id=admin.id)
    assert result["id"] > 0
    assert result["title"] == "Java工程师"


def test_list_position_templates(db_session):
    admin = _seed_admin(db_session)
    dictionary_service.create_position_template(
        PositionTemplateCreate(title="前端工程师", level="P4"), db_session, operator_id=admin.id
    )
    items = dictionary_service.list_position_templates(db_session)
    assert len(items) == 1


def test_create_skill_dict(db_session):
    req = SkillDictCreate(name="Spring Boot", category="backend")
    result = dictionary_service.create_skill(req, db_session)
    assert result["name"] == "Spring Boot"


def test_create_skill_duplicate(db_session):
    req = SkillDictCreate(name="Java", category="backend")
    dictionary_service.create_skill(req, db_session)
    with pytest.raises(AppError):
        dictionary_service.create_skill(req, db_session)


def test_list_skills_by_category(db_session):
    dictionary_service.create_skill(SkillDictCreate(name="React", category="frontend"), db_session)
    dictionary_service.create_skill(SkillDictCreate(name="Vue", category="frontend"), db_session)
    dictionary_service.create_skill(SkillDictCreate(name="Django", category="backend"), db_session)
    assert len(dictionary_service.list_skills(db_session, category="frontend")) == 2
    assert len(dictionary_service.list_skills(db_session, category="backend")) == 1
    assert len(dictionary_service.list_skills(db_session)) == 3


def test_create_competency_template_default(db_session):
    req = CompetencyTemplateCreate(
        name="标准面试模板",
        dimensions=[{"name": "专业技能"}, {"name": "沟通"}],
        is_default=True,
    )
    result = dictionary_service.create_competency_template(req, db_session)
    assert result["is_default"] is True
    default = dictionary_service.get_default_competency_template(db_session)
    assert default["name"] == "标准面试模板"


def test_only_one_default_competency(db_session):
    """设置新默认模板后，旧默认模板应被取消。"""
    dictionary_service.create_competency_template(
        CompetencyTemplateCreate(name="模板A", dimensions=[], is_default=True), db_session
    )
    dictionary_service.create_competency_template(
        CompetencyTemplateCreate(name="模板B", dimensions=[], is_default=True), db_session
    )
    default = dictionary_service.get_default_competency_template(db_session)
    assert default["name"] == "模板B"


def test_dictionary_api_read_all_roles(client, db_session):
    """所有已登录角色可读字典。"""
    db_session.add(User(username="hr_dict", password_hash=hash_password("x"), name="hr", role=Role.HR))
    db_session.commit()
    resp = client.post("/api/auth/login", json={"username": "hr_dict", "password": "x"})
    token = resp.json()["data"]["access_token"]
    resp = client.get("/api/dictionary/skills", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_dictionary_api_write_requires_admin(client, db_session):
    """非 ADMIN 无法写字典。"""
    db_session.add(User(username="hr_dict2", password_hash=hash_password("x"), name="hr2", role=Role.HR))
    db_session.commit()
    resp = client.post("/api/auth/login", json={"username": "hr_dict2", "password": "x"})
    token = resp.json()["data"]["access_token"]
    resp = client.post("/api/dictionary/skills",
                       json={"name": "Go", "category": "backend"},
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


# ── 批量异步评分 ──────────────────────────────────────────────────────────────


def test_batch_analyze_eager(db_session):
    """eager 模式下批量评分同步完成，结果落库。通过 patch get_llm_client 注入 MockClient。"""
    import unittest.mock as mock


    db_session.add(User(username="hr_batch", password_hash=hash_password("x"), name="hr", role=Role.HR))
    db_session.commit()

    req = JobDraftRequest(title="Java工程师", level="P5", business_req="")
    job_service.draft_job(req, db_session, operator_id=1, orchestrator=_job_orch(db_session))
    job = db_session.query(Job).first()

    up1 = resume_service.upload("cv1.txt", "Java 5年经验".encode(), db_session, operator_id=1, job_id=job.id)
    up2 = resume_service.upload("cv2.txt", "Python 3年经验".encode(), db_session, operator_id=1, job_id=job.id)

    mock_client = MockClient().with_response(
        "简历",
        {"match_score": 80, "advantages": ["扎实"], "risks": [], "rationale": {"hit": ["Java"]}},
    )

    with mock.patch("app.ai.orchestrator.get_llm_client", return_value=mock_client):
        from app.tasks.resume_tasks import analyze_resume_task

        for rid in [up1["resume_id"], up2["resume_id"]]:
            analyze_resume_task.delay(rid, job.id, operator_id=1)

    matches = db_session.query(ResumeMatchResult).all()
    assert len(matches) == 2
    assert all(0 <= m.match_score <= 100 for m in matches)


def test_batch_analyze_api(client, db_session):
    """POST /api/resumes/batch-analyze 返回 submitted 与 task_ids。"""
    import unittest.mock as mock


    db_session.add(User(username="hr_batch2", password_hash=hash_password("x"), name="hr2", role=Role.HR))
    db_session.commit()
    resp = client.post("/api/auth/login", json={"username": "hr_batch2", "password": "x"})
    token = resp.json()["data"]["access_token"]

    req = JobDraftRequest(title="产品经理", level="P6", business_req="")
    job_service.draft_job(req, db_session, operator_id=1, orchestrator=_job_orch(db_session))
    job = db_session.query(Job).first()
    up = resume_service.upload("cv.txt", "产品经验5年".encode(), db_session, operator_id=1, job_id=job.id)

    mock_client = MockClient().with_response(
        "简历",
        {"match_score": 70, "advantages": [], "risks": [], "rationale": {"hit": []}},
    )

    with mock.patch("app.ai.orchestrator.get_llm_client", return_value=mock_client):
        resp = client.post(
            "/api/resumes/batch-analyze",
            json={"resume_ids": [up["resume_id"]], "job_id": job.id},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["submitted"] == 1
    assert len(data["tasks"]) == 1
