"""AI 职位助手测试。覆盖 TC-301~309。"""
from app.ai.llm_client import MockClient
from app.ai.orchestrator import AgentOrchestrator
from app.common.security import hash_password
from app.models.enums import Role
from app.models.job import JdVersion, Job
from app.models.user import User
from app.schemas.job import JobDraftRequest, JobUpdateRequest
from app.services import job_service


def _login_token(client, db, username="hr"):
    db.add(User(username=username, password_hash=hash_password("x"), name=username, role=Role.HR))
    db.commit()
    resp = client.post("/api/auth/login", json={"username": username, "password": "x"})
    return resp.json()["data"]["access_token"]


def _mock_orchestrator(db):
    c = MockClient().with_response(
        "岗位",
        {
            "jd": {"title": "Java工程师", "responsibilities": ["开发"], "requirements": ["本科"]},
            "job_profile": {"方向": "后端", "年限": "3-5"},
            "skill_requirements": ["Java", "Spring"],
            "rationale": "依据岗位名称与等级推导",
        },
    )
    return AgentOrchestrator(db, client=c)


def test_draft_job_success(client, db_session):
    _login_token(client, db_session, "hr_t4_1")
    # 直接走 service 层注入 mock orchestrator，保证可复现且无外部依赖
    req = JobDraftRequest(title="Java工程师", level="P5", business_req="负责后端服务开发")
    result = job_service.draft_job(req, db_session, operator_id=1, orchestrator=_mock_orchestrator(db_session))
    assert result["job_id"] > 0
    assert result["jd"]["title"] == "Java工程师"
    assert result["rationale"]
    # 落库校验
    job = db_session.query(Job).first()
    assert job.title == "Java工程师"
    versions = db_session.query(JdVersion).filter_by(job_id=job.id).all()
    assert len(versions) == 1
    assert versions[0].source == "AI"


def test_draft_job_missing_field(client, db_session):
    token = _login_token(client, db_session, "hr_t4_2")
    # 缺 title -> 422
    resp = client.post(
        "/api/jobs/draft",
        json={"level": "P5", "business_req": "x"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_draft_job_without_token(client):
    resp = client.post("/api/jobs/draft", json={"title": "x", "level": "P5", "business_req": ""})
    assert resp.status_code == 401


def test_save_human_version(client, db_session):
    _login_token(client, db_session, "hr_t4_3")
    req = JobDraftRequest(title="前端工程师", level="P5", business_req="前端开发")
    job_service.draft_job(req, db_session, operator_id=1, orchestrator=_mock_orchestrator(db_session))
    job = db_session.query(Job).first()

    update_req = JobUpdateRequest(jd={"title": "前端工程师(已编辑)"})
    res = job_service.save_human_version(job.id, update_req, db_session, operator_id=1)
    assert res["source"] == "HUMAN"
    assert res["version_no"] == 2
    versions = db_session.query(JdVersion).filter_by(job_id=job.id).order_by(JdVersion.version_no).all()
    assert len(versions) == 2
    assert versions[1].source == "HUMAN"


def test_list_versions(client, db_session):
    _login_token(client, db_session, "hr_t4_4")
    req = JobDraftRequest(title="算法工程师", level="P6", business_req="")
    job_service.draft_job(req, db_session, operator_id=1, orchestrator=_mock_orchestrator(db_session))
    job = db_session.query(Job).first()
    versions = job_service.list_versions(job.id, db_session)
    assert len(versions) == 1
    assert versions[0]["source"] == "AI"


def test_get_job_not_found(client, db_session):
    token = _login_token(client, db_session, "hr_t4_5")
    resp = client.get("/api/jobs/9999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_draft_writes_audit(client, db_session):
    from app.models.ai_call_log import AiCallLog

    _login_token(client, db_session, "hr_t4_6")
    req = JobDraftRequest(title="测试工程师", level="P5", business_req="")
    job_service.draft_job(req, db_session, operator_id=1, orchestrator=_mock_orchestrator(db_session))
    logs = db_session.query(AiCallLog).filter_by(agent_type="JobAgent").all()
    assert len(logs) == 1
    assert logs[0].status == "success"


# ── RBAC 接口层测试 ────────────────────────────────────────────────────────


def _rbac_login(client, db, username, role, password="x"):
    """创建指定角色用户 → 登录 → 返回 token。"""
    db.add(User(username=username, password_hash=hash_password(password), name=username, role=role))
    db.commit()
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


def test_rbac_job_draft_interviewer_403(client, db_session):
    """INTERVIEWER 无权草拟 JD -> 403 (TC-309)。"""
    token = _rbac_login(client, db_session, "rbac_job_int", Role.INTERVIEWER)
    resp = client.post("/api/jobs/draft", json={"title": "x", "level": "P5", "business_req": ""},
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_rbac_job_draft_hr_200(client, db_session):
    """HR 可草拟 JD——但接口需 job_service 的 orchestrator 依赖，本次仅验证角色门禁放行。"""
    token = _rbac_login(client, db_session, "rbac_job_hr", Role.HR)
    resp = client.post("/api/jobs/draft", json={"title": "x", "level": "P5", "business_req": ""},
                       headers={"Authorization": f"Bearer {token}"})
    # 接口依赖真实 LLM（huawei/mock），未注入 orchestrator 时会 503；角色门禁应放行 → 200 或 503（LLM），不应 403
    assert resp.status_code in (200, 503)
