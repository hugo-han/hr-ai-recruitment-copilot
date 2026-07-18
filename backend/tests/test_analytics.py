"""招聘数据分析测试。覆盖 TC-601~605。"""
from app.ai.llm_client import MockClient
from app.ai.orchestrator import AgentOrchestrator
from app.common.security import hash_password
from app.models.enums import Role
from app.models.interview import COMPETENCY_TEMPLATE
from app.models.job import Job
from app.models.user import User
from app.schemas.interview import InterviewCreateRequest
from app.schemas.job import JobDraftRequest
from app.services import analytics_service, interview_service, job_service, resume_service


def _seed_user(db, username, role=Role.HR_LEAD):
    db.add(User(username=username, password_hash=hash_password("x"), name=username, role=role))
    db.commit()
    return db.query(User).filter_by(username=username).first()


def _job_orch(db):
    return AgentOrchestrator(db, client=MockClient().with_response(
        "岗位",
        {"jd": {"title": "Java工程师"}, "job_profile": {"方向": "后端"},
         "skill_requirements": ["Java", "Spring"], "rationale": "依据岗位"},
    ))


def _resume_orch(db, score=85):
    return AgentOrchestrator(db, client=MockClient().with_response(
        "简历",
        {"match_score": score, "advantages": ["扎实"], "risks": [], "rationale": {"hit": ["Java"]}},
    ))


def _eval_orch(db, recommendation="推荐"):
    payload = {
        "summary": "表现良好",
        "capability_eval": {d: "符合" for d in COMPETENCY_TEMPLATE},
        "recommendation": recommendation,
        "rationale": {"专业技能": "强"},
    }
    return AgentOrchestrator(db, client=MockClient().with_response("面试", payload))


def test_overview_empty_no_error(db_session):
    """无数据时不报错，返回空结构（TC-604）。"""
    result = analytics_service.get_overview(db_session)
    assert result["total_jobs"] == 0
    assert result["total_resumes"] == 0
    assert result["conversion_rate"]["uploaded"] == 0
    assert result["recruitment_cycle_days"] is None


def test_overview_full_funnel(db_session):
    """完整链路：岗位->简历->评分->面试->评价，转化率与周期计算正确（TC-601）。"""
    _seed_user(db_session, "lead_t8_1")
    req = JobDraftRequest(title="Java工程师", level="P5", business_req="")
    job_service.draft_job(req, db_session, operator_id=1, orchestrator=_job_orch(db_session))
    job = db_session.query(Job).first()

    up = resume_service.upload("cv.txt", "Java 5年经验".encode(), db_session, operator_id=1, job_id=job.id)
    resume_service.analyze(up["resume_id"], job.id, db_session, operator_id=1, orchestrator=_resume_orch(db_session))

    iv_req = InterviewCreateRequest(resume_id=up["resume_id"], job_id=job.id, record_text="面试记录")
    iid = interview_service.create_record(iv_req, db_session, operator_id=1)["interview_id"]
    interview_service.evaluate(iid, db_session, operator_id=1, orchestrator=_eval_orch(db_session))

    result = analytics_service.get_overview(db_session)
    assert result["total_jobs"] == 1
    assert result["total_resumes"] == 1
    assert result["total_interviews"] == 1
    cr = result["conversion_rate"]
    assert cr["uploaded"] == 1
    assert cr["analyzed"] == 1
    assert cr["interviewed"] == 1
    assert cr["evaluated"] == 1
    assert cr["recommended"] == 1
    assert cr["recommended_rate"] == 1.0
    assert result["recruitment_cycle_days"] is not None
    assert result["recruitment_cycle_days"] >= 0


def test_overview_time_filter(db_session):
    """按时间区间筛选（TC-602）：未来区间应筛出 0 条。"""
    from datetime import date, timedelta

    _seed_user(db_session, "lead_t8_2")
    req = JobDraftRequest(title="产品经理", level="P6", business_req="")
    job_service.draft_job(req, db_session, operator_id=1, orchestrator=_job_orch(db_session))

    future_start = date.today() + timedelta(days=30)
    result = analytics_service.get_overview(db_session, start=future_start)
    assert result["total_jobs"] == 0


def test_overview_api_requires_scope(client, db_session):
    """越权：HR 角色访问 analytics 应 403（TC-605）。"""
    db_session.add(User(username="hr_t8", password_hash=hash_password("x"), name="hr_t8", role=Role.HR))
    db_session.commit()
    resp = client.post("/api/auth/login", json={"username": "hr_t8", "password": "x"})
    token = resp.json()["data"]["access_token"]
    resp = client.get("/api/analytics/overview", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_overview_api_allows_hr_lead(client, db_session):
    _seed_user(db_session, "lead_t8_3")
    resp = client.post("/api/auth/login", json={"username": "lead_t8_3", "password": "x"})
    token = resp.json()["data"]["access_token"]
    resp = client.get("/api/analytics/overview", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


def test_overview_channel_effectiveness(db_session):
    """按渠道统计简历量与推荐率（TC-601 扩展：渠道效果）。"""
    _seed_user(db_session, "lead_t8_4")
    req = JobDraftRequest(title="Java工程师", level="P5", business_req="")
    job_service.draft_job(req, db_session, operator_id=1, orchestrator=_job_orch(db_session))
    job = db_session.query(Job).first()

    up1 = resume_service.upload(
        "cv1.txt", "Java 5年经验".encode(), db_session, operator_id=1, job_id=job.id,
        channel="INTERNAL_REFERRAL",
    )
    resume_service.analyze(up1["resume_id"], job.id, db_session, operator_id=1, orchestrator=_resume_orch(db_session))
    iv1 = interview_service.create_record(
        InterviewCreateRequest(resume_id=up1["resume_id"], job_id=job.id, record_text="面试记录1"),
        db_session, operator_id=1,
    )["interview_id"]
    interview_service.evaluate(iv1, db_session, operator_id=1, orchestrator=_eval_orch(db_session, "推荐"))

    up2 = resume_service.upload(
        "cv2.txt", "Python 3年经验".encode(), db_session, operator_id=1, job_id=job.id,
        channel="JOB_BOARD",
    )
    resume_service.analyze(up2["resume_id"], job.id, db_session, operator_id=1, orchestrator=_resume_orch(db_session, score=60))
    iv2 = interview_service.create_record(
        InterviewCreateRequest(resume_id=up2["resume_id"], job_id=job.id, record_text="面试记录2"),
        db_session, operator_id=1,
    )["interview_id"]
    interview_service.evaluate(iv2, db_session, operator_id=1, orchestrator=_eval_orch(db_session, "不推荐"))

    result = analytics_service.get_overview(db_session)
    ce = result["channel_effectiveness"]
    assert ce["INTERNAL_REFERRAL"]["uploaded"] == 1
    assert ce["INTERNAL_REFERRAL"]["recommended"] == 1
    assert ce["INTERNAL_REFERRAL"]["recommended_rate"] == 1.0
    assert ce["JOB_BOARD"]["uploaded"] == 1
    assert ce["JOB_BOARD"]["recommended"] == 0
    assert ce["JOB_BOARD"]["recommended_rate"] == 0.0


def test_upload_invalid_channel_falls_back_to_other(db_session):
    """非法渠道值兜底为 OTHER，不报错。"""
    from app.models.resume import Resume

    _seed_user(db_session, "lead_t8_5")
    resume_service.upload("cv.txt", b"x", db_session, operator_id=1, channel="NOT_A_REAL_CHANNEL")
    resume = db_session.query(Resume).first()
    assert resume.channel == "OTHER"


def test_overview_performance(db_session):
    """性能 ≤5s（TC-603）。"""
    import time

    start = time.time()
    analytics_service.get_overview(db_session)
    elapsed = time.time() - start
    assert elapsed <= 5
