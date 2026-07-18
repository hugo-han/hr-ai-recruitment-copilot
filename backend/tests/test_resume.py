"""AI 简历分析助手测试。覆盖 TC-401~413。"""
from app.ai.llm_client import MockClient
from app.ai.orchestrator import AgentOrchestrator
from app.common.redact import contains_plaintext_pii, mask_sensitive
from app.common.security import hash_password
from app.models.enums import Role
from app.models.job import Job
from app.models.resume import Resume, ResumeMatchResult
from app.models.user import User
from app.schemas.job import JobDraftRequest
from app.services import job_service, resume_service


def _seed_user(db, username="hr"):
    db.add(User(username=username, password_hash=hash_password("x"), name=username, role=Role.HR))
    db.commit()
    return db.query(User).filter_by(username=username).first()


def _seed_job(db):
    req = JobDraftRequest(title="Java工程师", level="P5", business_req="后端开发")
    job_service.draft_job(req, db, operator_id=1,
                          orchestrator=_job_orch(db))
    return db.query(Job).first()


def _job_orch(db):
    return AgentOrchestrator(db, client=MockClient().with_response(
        "岗位",
        {"jd": {"title": "Java工程师"}, "job_profile": {"方向": "后端"},
         "skill_requirements": ["Java", "Spring"], "rationale": "依据岗位"},
    ))


def _resume_orch(db):
    return AgentOrchestrator(db, client=MockClient().with_response(
        "简历",
        {"match_score": 85, "advantages": ["Java扎实"], "risks": ["无分布式经验"],
         "rationale": {"hit": ["Java"], "miss": ["分布式"]}},
    ))


def test_upload_txt_success(db_session):
    _seed_user(db_session, "hr_t5_1")
    res = resume_service.upload("cv.txt", "姓名:张三 技能:Java".encode(), db_session, operator_id=1)
    assert res["resume_id"] > 0
    assert "local://" in res["file_ref"]


def test_upload_invalid_format(db_session):
    import pytest

    from app.common.response import AppError

    with pytest.raises(AppError):
        resume_service.upload("malware.exe", b"x", db_session, operator_id=1)


def test_upload_pdf_accepted(db_session):
    _seed_user(db_session, "hr_t5_2")
    res = resume_service.upload("cv.pdf", b"%PDF-1.4 fake", db_session, operator_id=1)
    assert res["resume_id"] > 0


def test_analyze_success(db_session):
    _seed_user(db_session, "hr_t5_3")
    job = _seed_job(db_session)
    up = resume_service.upload("cv.txt", "技能:Java 5年经验".encode(), db_session, operator_id=1)
    result = resume_service.analyze(up["resume_id"], job.id, db_session, operator_id=1,
                                    orchestrator=_resume_orch(db_session))
    assert result["match_score"] == 85
    assert result["advantages"]
    assert result["risks"]
    assert "hit" in result["rationale"]
    match = db_session.query(ResumeMatchResult).first()
    assert match.match_score == 85


def test_analyze_resume_not_found(db_session):
    import pytest

    from app.common.response import AppError

    _seed_user(db_session, "hr_t5_4")
    _seed_job(db_session)
    with pytest.raises(AppError):
        resume_service.analyze(9999, 1, db_session, operator_id=1)


def test_analyze_score_range(db_session):
    """评分必须 0-100。"""
    _seed_user(db_session, "hr_t5_5")
    job = _seed_job(db_session)
    up = resume_service.upload("cv.txt", "技能:Java".encode(), db_session, operator_id=1)
    # 注入一个超界评分的 mock
    orch = AgentOrchestrator(db_session, client=MockClient().with_response(
        "简历", {"match_score": 150, "advantages": [], "risks": [], "rationale": {"hit": [], "miss": []}},
    ))
    import pytest

    from app.common.response import AppError

    with pytest.raises(AppError):
        resume_service.analyze(up["resume_id"], job.id, db_session, operator_id=1, orchestrator=orch)


def test_redact_pii():
    text = "身份证号110101199001011234，手机13800138000，邮箱a@b.com"
    masked = mask_sensitive(text)
    assert not contains_plaintext_pii(masked)
    assert "110101199001011234" not in masked
    assert "13800138000" not in masked


def test_analyze_writes_audit(db_session):
    from app.models.ai_call_log import AiCallLog

    _seed_user(db_session, "hr_t5_6")
    job = _seed_job(db_session)
    up = resume_service.upload("cv.txt", "技能:Java".encode(), db_session, operator_id=1)
    resume_service.analyze(up["resume_id"], job.id, db_session, operator_id=1,
                          orchestrator=_resume_orch(db_session))
    logs = db_session.query(AiCallLog).filter_by(agent_type="ResumeAgent").all()
    assert len(logs) == 1
    assert logs[0].status == "success"


def test_delete_resume_soft(db_session):
    _seed_user(db_session, "hr_t5_7")
    up = resume_service.upload("cv.txt", b"x", db_session, operator_id=1)
    res = resume_service.delete_resume(up["resume_id"], db_session, operator_id=1)
    assert res["deleted"] is True
    resume = db_session.query(Resume).first()
    assert resume.deleted == 1
    # 永久保留：记录仍在，文件未物理删除


def test_delete_resume_twice_conflict(db_session):
    import pytest

    from app.common.response import AppError

    _seed_user(db_session, "hr_t5_8")
    up = resume_service.upload("cv.txt", b"x", db_session, operator_id=1)
    resume_service.delete_resume(up["resume_id"], db_session, operator_id=1)
    with pytest.raises(AppError):
        resume_service.delete_resume(up["resume_id"], db_session, operator_id=1)


def test_export_resume(db_session):
    _seed_user(db_session, "hr_t5_9")
    up = resume_service.upload("cv.txt", b"my resume content", db_session, operator_id=1)
    res = resume_service.export_resume(up["resume_id"], db_session)
    assert res["size"] == len(b"my resume content")
    assert bytes.fromhex(res["content_b64"]) == b"my resume content"


def test_export_resume_writes_audit(db_session):
    """导出操作写入 AuditLog。对应 TC-705。"""
    from app.models.audit_log import AuditLog

    _seed_user(db_session, "hr_t5_14")
    up = resume_service.upload("cv.txt", b"content", db_session, operator_id=1)
    res = resume_service.export_resume_with_audit(up["resume_id"], db_session, operator_id=1)
    assert res["resume_id"] == up["resume_id"]
    logs = db_session.query(AuditLog).filter_by(action="export", resource_type="resume", resource_id=up["resume_id"]).all()
    assert len(logs) == 1
    assert logs[0].operator_id == 1


def test_export_api_writes_audit(client, db_session):
    """API 导出操作写入 AuditLog。"""
    from app.models.audit_log import AuditLog

    # export 需要 HR_LEAD 或 ADMIN 角色
    db_session.add(User(username="hr_t5_15", password_hash=hash_password("x"), name="hr_lead", role=Role.HR_LEAD))
    db_session.commit()
    up = resume_service.upload("cv.txt", b"test export audit", db_session, operator_id=1)

    resp = client.post("/api/auth/login", json={"username": "hr_t5_15", "password": "x"})
    token = resp.json()["data"]["access_token"]

    resp = client.get(f"/api/resumes/{up['resume_id']}/export", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    logs = db_session.query(AuditLog).filter_by(action="export", resource_type="resume", resource_id=up["resume_id"]).all()
    assert len(logs) == 1


def test_list_sort_by_score(db_session):
    _seed_user(db_session, "hr_t5_10")
    job = _seed_job(db_session)
    up1 = resume_service.upload("cv1.txt", b"Java", db_session, operator_id=1)
    up2 = resume_service.upload("cv2.txt", b"Python", db_session, operator_id=1)
    # 分别评分 85 / 60
    orch85 = AgentOrchestrator(db_session, client=MockClient().with_response(
        "简历", {"match_score": 85, "advantages": [], "risks": [], "rationale": {"hit": []}},
    ))
    resume_service.analyze(up1["resume_id"], job.id, db_session, operator_id=1, orchestrator=orch85)
    orch60 = AgentOrchestrator(db_session, client=MockClient().with_response(
        "简历", {"match_score": 60, "advantages": [], "risks": [], "rationale": {"hit": []}},
    ))
    resume_service.analyze(up2["resume_id"], job.id, db_session, operator_id=1, orchestrator=orch60)
    items = resume_service.list_resumes(db_session, sort_by_score=True)
    scores = [it["match_score"] for it in items if it["match_score"] is not None]
    assert scores == sorted(scores, reverse=True)


# ── F5.3 候选人状态流转 ────────────────────────────────────────────────────


def test_transition_pending_to_interview(db_session):
    _seed_user(db_session, "hr_t5_11")
    up = resume_service.upload("cv.txt", b"x", db_session, operator_id=1)
    result = resume_service.transition_status(up["resume_id"], "interview", db_session, operator_id=1)
    assert result["old_status"] == "pending"
    assert result["new_status"] == "interview"


def test_transition_invalid_jump(db_session):
    import pytest

    from app.common.response import AppError

    _seed_user(db_session, "hr_t5_12")
    up = resume_service.upload("cv.txt", b"x", db_session, operator_id=1)
    with pytest.raises(AppError):
        resume_service.transition_status(up["resume_id"], "hired", db_session, operator_id=1)


def test_transition_api(client, db_session):
    _seed_user(db_session, "hr_t5_13")
    up = resume_service.upload("cv.txt", b"x", db_session, operator_id=1)

    resp = client.post("/api/auth/login", json={"username": "hr_t5_13", "password": "x"})
    token = resp.json()["data"]["access_token"]

    resp = client.put(
        f"/api/resumes/{up['resume_id']}/status",
        json={"target_status": "interview"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["new_status"] == "interview"

    # 非法跳转：pending → hired（跳过 interview）
    up2 = resume_service.upload("cv2.txt", b"y", db_session, operator_id=1)
    resp = client.put(
        f"/api/resumes/{up2['resume_id']}/status",
        json={"target_status": "hired"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


# ── RBAC 接口层测试 (TC-908) ──────────────────────────────────────────────


def _api_login(client, db_session, username, role, password="x"):
    """创建用户 → 登录 → 返回 access_token。"""
    db_session.add(User(
        username=username, password_hash=hash_password(password),
        name=username, role=role,
    ))
    db_session.commit()
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


def _seed_resume_via_service(db_session):
    """通过 service 层创建一份简历（会实际写入 LocalObjectStorage，export 可读）。"""
    _seed_user(db_session, "rbac_owner")
    return resume_service.upload("cv.txt", b"test content", db_session, operator_id=1)


# ── DELETE RBAC ──


def test_rbac_delete_interviewer_403(client, db_session):
    token = _api_login(client, db_session, "rbac_del_int", Role.INTERVIEWER)
    resp = client.delete("/api/resumes/1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_rbac_delete_hr_403(client, db_session):
    token = _api_login(client, db_session, "rbac_del_hr", Role.HR)
    resp = client.delete("/api/resumes/1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_rbac_delete_hr_lead_200(client, db_session):
    token = _api_login(client, db_session, "rbac_del_lead", Role.HR_LEAD)
    up = _seed_resume_via_service(db_session)
    resp = client.delete(f"/api/resumes/{up['resume_id']}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


def test_rbac_delete_admin_200(client, db_session):
    token = _api_login(client, db_session, "rbac_del_admin", Role.ADMIN)
    up = _seed_resume_via_service(db_session)
    resp = client.delete(f"/api/resumes/{up['resume_id']}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


def test_rbac_delete_no_token_401(client, db_session):
    _seed_resume_via_service(db_session)
    resp = client.delete("/api/resumes/1")
    assert resp.status_code == 401


# ── EXPORT RBAC ──


def test_rbac_export_interviewer_403(client, db_session):
    token = _api_login(client, db_session, "rbac_exp_int", Role.INTERVIEWER)
    resp = client.get("/api/resumes/1/export", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_rbac_export_hr_403(client, db_session):
    token = _api_login(client, db_session, "rbac_exp_hr", Role.HR)
    resp = client.get("/api/resumes/1/export", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_rbac_export_hr_lead_200(client, db_session):
    token = _api_login(client, db_session, "rbac_exp_lead", Role.HR_LEAD)
    up = _seed_resume_via_service(db_session)
    resp = client.get(f"/api/resumes/{up['resume_id']}/export", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


def test_rbac_export_admin_200(client, db_session):
    token = _api_login(client, db_session, "rbac_exp_admin", Role.ADMIN)
    up = _seed_resume_via_service(db_session)
    resp = client.get(f"/api/resumes/{up['resume_id']}/export", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


# ── UPLOAD & ANALYZE RBAC ──


def test_rbac_upload_interviewer_403(client, db_session):
    """INTERVIEWER 无权上传简历 -> 403。"""
    token = _api_login(client, db_session, "rbac_up_int", Role.INTERVIEWER)
    resp = client.post("/api/resumes/upload", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_rbac_analyze_interviewer_403(client, db_session):
    """INTERVIEWER 无权做简历评分 -> 403。"""
    token = _api_login(client, db_session, "rbac_an_int", Role.INTERVIEWER)
    resp = client.post("/api/resumes/1/analyze", json={"job_id": 1},
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
