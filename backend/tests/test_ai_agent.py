"""AI Agent 基座测试。覆盖 TC-201~210。"""
from app.ai.llm_client import MockClient, digest_text
from app.ai.orchestrator import AgentContext, AgentOrchestrator
from app.ai.output_parser import parse_json_object, require_rationale
from app.models.ai_call_log import AiCallLog


def test_mock_client_returns_structured():
    client = MockClient().with_response(
        "JD",
        {"jd": "...", "job_profile": "...", "skill_requirements": [], "rationale": "基于岗位信息"},
    )
    messages = [{"role": "user", "content": "请生成JD"}]
    result = client.chat(messages, schema={"type": "object"})
    assert result.parsed is not None
    assert result.parsed["rationale"]


def test_prompt_manager_versioned():
    from app.ai.prompt_manager import get_prompt

    p = get_prompt("job_draft")
    assert p.version == "v1"
    assert "{title}" in p.user_template


def test_output_parser_valid_json():
    data = parse_json_object('{"a": 1, "rationale": "x"}')
    assert data["a"] == 1


def test_output_parser_codeblock_wrapped():
    data = parse_json_object('```json\n{"a": 2, "rationale": "y"}\n```')
    assert data["a"] == 2


def test_output_parser_invalid_json():
    from app.common.response import AppError

    try:
        parse_json_object("not json")
        raise AssertionError("应抛异常")
    except AppError as exc:
        assert exc.code == 502


def test_require_rationale_missing():
    from app.common.response import AppError

    try:
        require_rationale({"a": 1})
        raise AssertionError("应抛异常")
    except AppError as exc:
        assert exc.code == 502


def test_orchestrator_writes_audit_log(db_session):
    client = MockClient().with_response(
        "JD",
        {"jd": "jd", "job_profile": "p", "skill_requirements": [], "rationale": "依据"},
    )
    orch = AgentOrchestrator(db_session, client=client)
    ctx = AgentContext(agent_type="JobAgent", operator_id=1, prompt_name="job_draft")
    result = orch.invoke(ctx, "请生成JD", schema={"type": "object"})
    assert result["rationale"] == "依据"
    logs = db_session.query(AiCallLog).all()
    assert len(logs) == 1
    assert logs[0].agent_type == "JobAgent"
    assert logs[0].status == "success"
    assert logs[0].operator_id == 1


def test_orchestrator_logs_failure(db_session):
    client = MockClient()  # 无预设响应 -> _default -> parsed=None -> 解析失败
    orch = AgentOrchestrator(db_session, client=client)
    ctx = AgentContext(agent_type="JobAgent", operator_id=1, prompt_name="job_draft")
    from app.common.response import AppError

    try:
        orch.invoke(ctx, "无关内容", schema={"type": "object"})
        raise AssertionError("应抛异常")
    except AppError:
        pass
    logs = db_session.query(AiCallLog).all()
    assert any(item.status == "failed" for item in logs)


def test_audit_log_no_plaintext(db_session):
    """审计日志只存摘要，不含明文输入。"""
    secret = "我的身份证号110101199001011234"
    client = MockClient().with_response(
        "JD",
        {"jd": "x", "job_profile": "p", "skill_requirements": [], "rationale": "r"},
    )
    orch = AgentOrchestrator(db_session, client=client)
    ctx = AgentContext(agent_type="JobAgent", operator_id=1, prompt_name="job_draft")
    orch.invoke(ctx, f"包含敏感信息 {secret}，请生成JD", schema={"type": "object"})
    log = db_session.query(AiCallLog).first()
    assert "110101199001011234" not in (log.input_digest or "")
    assert log.input_digest == digest_text(f"包含敏感信息 {secret}，请生成JD")
