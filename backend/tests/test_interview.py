"""AI 面试助手测试。覆盖 TC-501~509。"""
import pytest

from app.ai.llm_client import MockClient
from app.ai.orchestrator import AgentOrchestrator
from app.common.response import AppError
from app.common.security import hash_password
from app.models.enums import Role
from app.models.interview import COMPETENCY_TEMPLATE, Interview, InterviewEval
from app.models.user import User
from app.schemas.interview import InterviewCreateRequest
from app.services import interview_service


def _seed_user(db, username="iv"):
    db.add(User(username=username, password_hash=hash_password("x"), name=username, role=Role.INTERVIEWER))
    db.commit()
    return db.query(User).filter_by(username=username).first()


def _eval_orch(db):
    payload = {
        "summary": "候选人整体表现良好",
        "capability_eval": {d: "符合" for d in COMPETENCY_TEMPLATE},
        "recommendation": "推荐",
        "rationale": {"专业技能": "强", "沟通": "良"},
    }
    return AgentOrchestrator(db, client=MockClient().with_response("面试", payload))


def test_create_record(db_session):
    _seed_user(db_session, "iv_t6_1")
    req = InterviewCreateRequest(record_text="面试过程记录...")
    res = interview_service.create_record(req, db_session, operator_id=1)
    assert res["interview_id"] > 0
    assert res["status"] == "recorded"
    assert db_session.query(Interview).count() == 1


def test_create_record_empty(db_session):
    """空记录应 422（Pydantic 校验抛 ValidationError）。"""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        InterviewCreateRequest(record_text="")


def test_evaluate_success(db_session):
    _seed_user(db_session, "iv_t6_2")
    req = InterviewCreateRequest(record_text="面试记录内容")
    iid = interview_service.create_record(req, db_session, operator_id=1)["interview_id"]
    result = interview_service.evaluate(iid, db_session, operator_id=1, orchestrator=_eval_orch(db_session))
    assert result["recommendation"] == "推荐"
    assert result["rationale"]
    assert set(result["capability_eval"].keys()) >= set(COMPETENCY_TEMPLATE)
    ev = db_session.query(InterviewEval).first()
    assert ev.recommendation == "推荐"
    assert db_session.get(Interview, iid).status == "evaluated"


def test_evaluate_not_found(db_session):
    _seed_user(db_session, "iv_t6_3")
    with pytest.raises(AppError):
        interview_service.evaluate(9999, db_session, operator_id=1, orchestrator=_eval_orch(db_session))


def test_evaluate_invalid_recommendation(db_session):
    _seed_user(db_session, "iv_t6_4")
    req = InterviewCreateRequest(record_text="面试记录")
    iid = interview_service.create_record(req, db_session, operator_id=1)["interview_id"]
    orch = AgentOrchestrator(db_session, client=MockClient().with_response(
        "面试",
        {"summary": "x", "capability_eval": {d: "y" for d in COMPETENCY_TEMPLATE},
         "recommendation": "未知", "rationale": {"x": 1}},
    ))
    with pytest.raises(AppError):
        interview_service.evaluate(iid, db_session, operator_id=1, orchestrator=orch)


def test_evaluate_missing_dimension(db_session):
    _seed_user(db_session, "iv_t6_5")
    req = InterviewCreateRequest(record_text="面试记录")
    iid = interview_service.create_record(req, db_session, operator_id=1)["interview_id"]
    incomplete = {d: "y" for d in COMPETENCY_TEMPLATE}
    incomplete.pop("学习能力")
    orch = AgentOrchestrator(db_session, client=MockClient().with_response(
        "面试",
        {"summary": "x", "capability_eval": incomplete, "recommendation": "待定", "rationale": {"x": 1}},
    ))
    with pytest.raises(AppError):
        interview_service.evaluate(iid, db_session, operator_id=1, orchestrator=orch)


def test_evaluate_writes_audit(db_session):
    from app.models.ai_call_log import AiCallLog

    _seed_user(db_session, "iv_t6_6")
    req = InterviewCreateRequest(record_text="面试记录")
    iid = interview_service.create_record(req, db_session, operator_id=1)["interview_id"]
    interview_service.evaluate(iid, db_session, operator_id=1, orchestrator=_eval_orch(db_session))
    logs = db_session.query(AiCallLog).filter_by(agent_type="InterviewAgent").all()
    assert len(logs) == 1
    assert logs[0].status == "success"


def test_create_via_api_requires_token(client, db_session):
    resp = client.post("/api/interviews", json={"record_text": "x"})
    assert resp.status_code == 401


# ── F3.5 面试问题建议 ───────────────────────────────────────────────────────


def test_suggest_questions_success(db_session):
    """基于岗位信息生成面试问题建议。"""
    from app.models.job import Job

    _seed_user(db_session, "iv_t6_7")
    job = Job(title="Java工程师", level="P5", business_req="后端开发", status="draft", created_by=1)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # MockClient 默认响应中包含 "面试" key，suggest_questions 的提示词含 "技能" 关键词
    # 需要 match 到，所以使用 _eval_orch 的面试响应风格
    orch = _eval_orch(db_session)
    result = interview_service.suggest_questions(job.id, db_session, operator_id=1, orchestrator=orch)
    assert result["job_id"] == job.id
    assert "questions" in result


def test_suggest_questions_job_not_found(db_session):
    _seed_user(db_session, "iv_t6_8")
    with pytest.raises(AppError):
        interview_service.suggest_questions(9999, db_session, operator_id=1)


def test_suggest_questions_api(client, db_session):
    from app.models.job import Job

    db_session.add(User(username="iv_t6_9", password_hash=hash_password("x"), name="iv_t6_9", role=Role.INTERVIEWER))
    db_session.commit()
    resp = client.post("/api/auth/login", json={"username": "iv_t6_9", "password": "x"})
    token = resp.json()["data"]["access_token"]

    job = Job(title="产品经理", level="P6", business_req="", status="draft", created_by=1)
    db_session.add(job)
    db_session.commit()

    resp = client.get(f"/api/interviews/suggest-questions/{job.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["job_id"] == job.id


# ── RBAC 接口层测试 ────────────────────────────────────────────────────────


def _rbac_login(client, db, username, role, password="x"):
    """创建指定角色用户 → 登录 → 返回 token。"""
    db.add(User(username=username, password_hash=hash_password(password), name=username, role=role))
    db.commit()
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


def test_rbac_interview_create_hr_200(client, db_session):
    """HR 可录入面试记录（INTERVIEWER+ 包含 HR）-> 200。"""
    token = _rbac_login(client, db_session, "rbac_iv_hr", Role.HR)
    resp = client.post("/api/interviews", json={"record_text": "x"},
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
