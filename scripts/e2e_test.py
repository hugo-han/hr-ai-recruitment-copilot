#!/usr/bin/env python3
"""
HR 招聘 AI 助手 — 前端 E2E 功能测试（API 层）
测试账号：admin/hr/hr_lead/interviewer（真实账号，后端 http://localhost:8000）
对应 test-case.md TC-FE-* 与 PRD AC-US-01~08
"""
import json
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"
RESULTS: list[dict] = []


# ──────────────────── helpers ────────────────────

def req(method: str, path: str, data: Any = None, token: str = "") -> tuple[int, dict]:
    url = BASE + path
    body = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {}


def login(username: str, password: str) -> str:
    _, d = req("POST", "/api/auth/login", {"username": username, "password": password})
    return d.get("data", {}).get("access_token", "")


def record(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    sym = "✅" if passed else "❌"
    print(f"  {sym} {status:4s} | {name}" + (f" — {detail}" if detail else ""))
    RESULTS.append({"name": name, "passed": passed, "detail": detail})


def section(title: str):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ──────────────────── TC groups ────────────────────

def test_auth():
    section("1. 鉴权与登录（TC-101~108）")

    # 正确登录 4 账号
    for user, pwd, expected_role in [
        ("admin", "admin123", "ADMIN"),
        ("hr", "hr123", "HR"),
        ("hr_lead", "lead123", "HR_LEAD"),
        ("interviewer", "iv123", "INTERVIEWER"),
    ]:
        _, d = req("POST", "/api/auth/login", {"username": user, "password": pwd})
        role = d.get("data", {}).get("role", "")
        tok = d.get("data", {}).get("access_token", "")
        record(f"TC-101 {user} 登录", d.get("code") == 0 and role == expected_role and bool(tok),
               f"role={role}")

    # 密码错误 → 401
    code, _ = req("POST", "/api/auth/login", {"username": "hr", "password": "wrong"})
    record("TC-102 密码错误 401", code == 401, f"HTTP {code}")

    # 无 token 访问受保护接口 → 401
    code, _ = req("POST", "/api/jobs/draft", {"title": "x", "level": "P5", "business_req": "x"})
    record("TC-103 无 token 访问 401", code == 401, f"HTTP {code}")

    # /api/auth/me 验证 token 有效
    tok = login("hr", "hr123")
    code, d = req("GET", "/api/auth/me", token=tok)
    record("TC-105 /me 返回用户信息", code == 200 and d.get("data", {}).get("username") == "hr",
           f"username={d.get('data',{}).get('username')}")


def test_menu_rbac() -> dict:
    section("2. 菜单 RBAC（Issue #4 修复验证，TC-FE-MENU-*）")
    # 通过 ROLE_PERMISSIONS 约定验证：HR 无 analytics，其他有
    tokens = {
        "HR": login("hr", "hr123"),
        "HR_LEAD": login("hr_lead", "lead123"),
        "INTERVIEWER": login("interviewer", "iv123"),
        "ADMIN": login("admin", "admin123"),
    }

    # HR → analytics 应 403
    code, _ = req("GET", "/api/analytics/overview", token=tokens["HR"])
    record("TC-FE-MENU-HR: analytics 返回 403", code == 403, f"HTTP {code}")

    # HR_LEAD → analytics 应 200
    code, d = req("GET", "/api/analytics/overview", token=tokens["HR_LEAD"])
    record("TC-FE-MENU-HRLEAD: analytics 返回 200", code == 200 and d.get("code") == 0, f"HTTP {code}")

    # INTERVIEWER → job draft 应 403
    code, _ = req("POST", "/api/jobs/draft",
                  {"title": "x", "level": "P5", "business_req": "x"},
                  token=tokens["INTERVIEWER"])
    record("TC-FE-MENU-ITV: job draft 返回 403", code == 403, f"HTTP {code}")

    # ADMIN → analytics + dictionary 均应 200
    code, _ = req("GET", "/api/analytics/overview", token=tokens["ADMIN"])
    record("TC-FE-MENU-ADMIN: analytics 返回 200", code == 200, f"HTTP {code}")
    code, _ = req("GET", "/api/dictionary/skills", token=tokens["ADMIN"])
    record("TC-FE-MENU-ADMIN: dictionary 返回 200", code == 200, f"HTTP {code}")

    return tokens


def test_job_workflow(tokens: dict) -> int:
    section("3. AI 职位助手（TC-301~309 / AC-US-01）")
    tok = tokens["HR"]
    job_id = 0

    # JD 生成
    code, d = req("POST", "/api/jobs/draft",
                  {"title": "高级Python工程师", "level": "P7",
                   "business_req": "负责后端微服务架构，需要5年Python/FastAPI经验"},
                  token=tok)
    ok = code == 200 and d.get("code") == 0
    data = d.get("data", {})
    job_id = data.get("job_id", 0)
    has_jd = bool(data.get("jd"))
    has_rationale = bool(data.get("rationale"))
    record("TC-301 JD 生成 code=0", ok, f"job_id={job_id}")
    record("TC-302 输出含 jd/job_profile/skill_requirements", has_jd and bool(data.get("job_profile")),
           f"keys={list(data.keys())}")
    record("TC-303 输出含 rationale（可解释依据）", has_rationale, f"rationale={str(data.get('rationale',''))[:40]}")

    if job_id:
        # GET 岗位详情
        code, d = req("GET", f"/api/jobs/{job_id}", token=tok)
        record("TC-301b GET 岗位详情", code == 200 and d.get("data", {}).get("id") == job_id,
               f"status={d.get('data',{}).get('status')}")

        # 编辑 JD（版本留痕）
        code, d = req("PUT", f"/api/jobs/{job_id}",
                      {"jd": {"title": "高级Python工程师（已编辑）", "responsibilities": ["架构设计"]}},
                      token=tok)
        record("TC-306 JD 编辑版本留痕 source=HUMAN",
               code == 200 and d.get("data", {}).get("source") == "HUMAN",
               f"version={d.get('data',{}).get('version_no')}")

        # 版本列表
        code, d = req("GET", f"/api/jobs/{job_id}/versions", token=tok)
        record("TC-306b 版本列表 ≥2", code == 200 and len(d.get("data", [])) >= 2,
               f"versions={len(d.get('data',[]))}")

    # 缺字段校验
    code, _ = req("POST", "/api/jobs/draft", {"level": "P5", "business_req": "x"}, token=tok)
    record("TC-305 缺 title 返回 422", code == 422, f"HTTP {code}")

    # Interviewer 无权访问 draft
    code, _ = req("POST", "/api/jobs/draft",
                  {"title": "x", "level": "P5", "business_req": "x"},
                  token=tokens["INTERVIEWER"])
    record("TC-309 INTERVIEWER 访问 draft 403", code == 403, f"HTTP {code}")

    return job_id


def test_resume_workflow(tokens: dict, job_id: int) -> int:
    section("4. AI 简历分析助手（TC-401~413 / AC-US-02）")
    tok = tokens["HR"]
    resume_id = 0

    # 上传简历（multipart）
    boundary = "QATestBoundary1234"
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"candidate_cv.txt\"\r\n"
        f"Content-Type: text/plain\r\n\r\n"
        f"姓名：李明\n技能：Python FastAPI SQLAlchemy Docker Kubernetes\n"
        f"工作经验：6年后端开发，主导3个微服务项目\n教育：本科计算机科学\n"
        f"\r\n--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"job_id\"\r\n\r\n{job_id}\r\n"
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"channel\"\r\n\r\n社招\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {tok}",
    }
    r = urllib.request.Request(BASE + "/api/resumes/upload", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            d = json.loads(resp.read())
        code = 200
    except urllib.error.HTTPError as e:
        code = e.code; d = {}

    resume_id = d.get("data", {}).get("resume_id", 0)
    record("TC-401 简历上传成功", code == 200 and resume_id > 0, f"resume_id={resume_id}")

    if resume_id and job_id:
        # 分析评分
        code, d = req("POST", f"/api/resumes/{resume_id}/analyze",
                      {"job_id": job_id}, token=tok)
        data = d.get("data", {})
        score = data.get("match_score", -1)
        ok = code == 200 and 0 <= score <= 100
        record("TC-406 匹配评分 0–100", ok, f"score={score}")
        record("TC-407 输出优势/风险", bool(data.get("advantages")) or bool(data.get("risks")),
               f"adv={data.get('advantages','')[:30]}")
        record("TC-408 评分含 rationale（命中/缺失）", bool(data.get("rationale")),
               f"rationale={str(data.get('rationale',''))[:40]}")

    # 非法格式上传
    body2 = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"malware.exe\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\nfake binary\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    r2 = urllib.request.Request(BASE + "/api/resumes/upload", data=body2,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                                          "Authorization": f"Bearer {tok}"},
                                 method="POST")
    try:
        with urllib.request.urlopen(r2, timeout=10) as resp:
            code2, d2 = resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        code2 = e.code; d2 = {}
    record("TC-403 .exe 格式被拒绝 400", code2 == 400, f"HTTP {code2}")

    # 列表按评分排序
    code, d = req("GET", "/api/resumes?sort=score", token=tok)
    items = d.get("data", [])
    scores = [i.get("match_score") for i in items if i.get("match_score") is not None]
    sorted_ok = scores == sorted(scores, reverse=True)
    record("TC-411 简历列表按评分降序", code == 200 and sorted_ok,
           f"scores={scores}")

    # 删除权限（HR 应 403）
    if resume_id:
        code, _ = req("DELETE", f"/api/resumes/{resume_id}", token=tok)
        record("TC-703 HR 删除简历 403", code == 403, f"HTTP {code}")

    return resume_id


def test_interview_workflow(tokens: dict, resume_id: int, job_id: int) -> int:
    section("5. AI 面试助手（TC-501~509 / AC-US-03）")
    tok = tokens["INTERVIEWER"]
    hr = tokens["HR"]
    iv_id = 0

    # 面试官创建面试记录（通过 Python urllib 保证 UTF-8 编码）
    payload = json.dumps({
        "resume_id": resume_id,
        "job_id": job_id,
        "record_text": "候选人Python功底深厚，对FastAPI异步机制理解到位，"
                       "能讲清微服务拆分原则，沟通表达清晰流畅，团队协作意愿强"
    }).encode("utf-8")
    r = urllib.request.Request(
        BASE + "/api/interviews",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            d = json.loads(resp.read()); code = 200
    except urllib.error.HTTPError as e:
        code = e.code; d = {}

    iv_id = d.get("data", {}).get("interview_id", 0)
    record("TC-501 录入面试记录", code == 200 and iv_id > 0, f"interview_id={iv_id}")

    if iv_id:
        # 生成评价
        eval_payload = json.dumps({}).encode("utf-8")
        r2 = urllib.request.Request(
            BASE + f"/api/interviews/{iv_id}/evaluate",
            data=eval_payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(r2, timeout=30) as resp:
                d2 = json.loads(resp.read()); code2 = 200
        except urllib.error.HTTPError as e:
            code2 = e.code; d2 = {}

        data = d2.get("data", {})
        rec = data.get("recommendation", "")
        record("TC-502 评价生成 code=0", code2 == 200 and d2.get("code") == 0, f"HTTP {code2}")
        record("TC-503 推荐为三选一", rec in ("推荐", "待定", "不推荐"), f"recommendation={rec}")
        record("TC-504 能力评价含维度", bool(data.get("capability_eval")),
               f"dims={list(data.get('capability_eval',{}).keys())[:3]}")
        record("TC-505 含 rationale", bool(data.get("rationale")),
               f"rationale={str(data.get('rationale',''))[:40]}")

    # 空 record_text 应 422
    empty_payload = json.dumps({"resume_id": 1, "job_id": 1, "record_text": ""}).encode("utf-8")
    r3 = urllib.request.Request(
        BASE + "/api/interviews",
        data=empty_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(r3, timeout=10) as resp:
            code3 = resp.status
    except urllib.error.HTTPError as e:
        code3 = e.code
    record("TC-506 空记录 422", code3 == 422, f"HTTP {code3}")

    # TC-F35: suggest-questions（MockClient 返回空列表为正常，验证接口可达、code=0）
    if job_id:
        code4, d4 = req("GET", f"/api/interviews/suggest-questions/{job_id}", token=tok)
        ok_reach = code4 == 200 and d4.get("code") == 0
        record("TC-F35 面试问题建议接口可达（F3.5）",
               ok_reach,
               f"HTTP {code4} code={d4.get('code')} questions={len(d4.get('data',{}).get('questions',[]))}")

    return iv_id


def test_status_flow(tokens: dict, resume_id: int):
    section("6. 候选人状态流转（TC-F53 / F5.3）")
    tok = tokens["HR"]

    # pending → interview
    payload = json.dumps({"target_status": "interview"}).encode("utf-8")
    r = urllib.request.Request(
        BASE + f"/api/resumes/{resume_id}/status",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"},
        method="PUT"
    )
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            d = json.loads(resp.read()); code = 200
    except urllib.error.HTTPError as e:
        code = e.code; d = {}
    record("TC-F53 pending→interview 成功",
           code == 200 and d.get("data", {}).get("new_status") == "interview",
           f"HTTP {code} new_status={d.get('data',{}).get('new_status')}")

    # interview → hired
    payload2 = json.dumps({"target_status": "hired"}).encode("utf-8")
    r2 = urllib.request.Request(
        BASE + f"/api/resumes/{resume_id}/status",
        data=payload2,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"},
        method="PUT"
    )
    try:
        with urllib.request.urlopen(r2, timeout=15) as resp:
            d2 = json.loads(resp.read()); code2 = 200
    except urllib.error.HTTPError as e:
        code2 = e.code; d2 = {}
    record("TC-F53b interview→hired 成功",
           code2 == 200 and d2.get("data", {}).get("new_status") == "hired",
           f"HTTP {code2} new_status={d2.get('data',{}).get('new_status')}")

    # hired → pending（非法跳转，应 409）
    payload3 = json.dumps({"target_status": "pending"}).encode("utf-8")
    r3 = urllib.request.Request(
        BASE + f"/api/resumes/{resume_id}/status",
        data=payload3,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"},
        method="PUT"
    )
    try:
        with urllib.request.urlopen(r3, timeout=15) as resp:
            code3 = resp.status
    except urllib.error.HTTPError as e:
        code3 = e.code
    record("TC-F53c hired→pending 非法跳转 409", code3 == 409, f"HTTP {code3}")


def test_analytics(tokens: dict):
    section("7. 数据分析看板（TC-601~605 / AC-US-04）")

    # HR_LEAD 可访问
    code, d = req("GET", "/api/analytics/overview", token=tokens["HR_LEAD"])
    data = d.get("data", {})
    cr = data.get("conversion_rate", {})
    record("TC-601 看板返回 ≥3 指标",
           code == 200 and all(k in data for k in ("recruitment_cycle_days", "conversion_rate", "channel_effectiveness")),
           f"jobs={data.get('total_jobs')} resumes={data.get('total_resumes')}")
    record("TC-601b 漏斗转化率字段完整",
           all(k in cr for k in ("uploaded", "analyzed", "interviewed", "evaluated", "recommended")),
           f"funnel={list(cr.keys())}")

    # 时间筛选（未来时间应返回 0）
    code, d = req("GET", "/api/analytics/overview?start=2030-01-01", token=tokens["HR_LEAD"])
    record("TC-602 时间筛选（未来区间返回 0）",
           code == 200 and d.get("data", {}).get("total_resumes", 1) == 0,
           f"HTTP {code} resumes={d.get('data',{}).get('total_resumes')}")

    # HR 无权访问（403）
    code, _ = req("GET", "/api/analytics/overview", token=tokens["HR"])
    record("TC-605 HR 访问 analytics 403", code == 403, f"HTTP {code}")

    # 性能（≤5s）
    t0 = time.time()
    req("GET", "/api/analytics/overview", token=tokens["HR_LEAD"])
    elapsed = time.time() - t0
    record("TC-603 看板查询 ≤5s", elapsed <= 5, f"{elapsed:.2f}s")


def test_dictionary(tokens: dict):
    section("8. 字典管理（T9 / F5.2）")

    # 所有角色可读
    for role, tok in [("HR", tokens["HR"]), ("INTERVIEWER", tokens["INTERVIEWER"])]:
        code, _ = req("GET", "/api/dictionary/skills", token=tok)
        record(f"TC-T9-READ {role} 可读字典", code == 200, f"HTTP {code}")

    # HR 不可写
    code, _ = req("POST", "/api/dictionary/skills",
                  {"name": "Go语言", "category": "backend"},
                  token=tokens["HR"])
    record("TC-T9-WRITE HR 写字典 403", code == 403, f"HTTP {code}")

    # ADMIN 可写
    code, d = req("POST", "/api/dictionary/skills",
                  {"name": f"Rust-{int(time.time())}", "category": "backend"},
                  token=tokens["ADMIN"])
    record("TC-T9-WRITE ADMIN 写字典成功", code == 200 and d.get("code") == 0, f"HTTP {code}")


def test_compliance(tokens: dict, resume_id: int):
    section("9. 合规与安全（TC-701~706 / AC-US-06/08）")

    # 导出（ADMIN/HR_LEAD 可）
    code, d = req("GET", f"/api/resumes/{resume_id}/export", token=tokens["ADMIN"])
    record("TC-704 ADMIN 导出简历",
           code == 200 and bool(d.get("data", {}).get("file_name")),
           f"file={d.get('data',{}).get('file_name')} size={d.get('data',{}).get('size')}")

    # 非授权角色导出（HR → 403）
    code, _ = req("GET", f"/api/resumes/{resume_id}/export", token=tokens["HR"])
    record("TC-704b HR 导出 403", code == 403, f"HTTP {code}")

    # INTERVIEWER 删除（403）
    code, _ = req("DELETE", f"/api/resumes/{resume_id}", token=tokens["INTERVIEWER"])
    record("TC-703 INTERVIEWER 删除 403", code == 403, f"HTTP {code}")

    # 审计日志可访问（AI 调用后 ai_call_log 有记录，通过 analytics 验证数据存在）
    code, d = req("GET", "/api/analytics/overview", token=tokens["ADMIN"])
    record("TC-F54 AI 调用可追溯（analytics 数据存在）",
           code == 200 and d.get("data", {}).get("total_jobs", 0) > 0,
           f"jobs={d.get('data',{}).get('total_jobs')}")


def test_ai_agent():
    section("10. AI 可解释性与 rationale（TC-AI-* / AC-US-01~03）")

    tok = login("hr", "hr123")
    code, d = req("POST", "/api/jobs/draft",
                  {"title": "数据工程师", "level": "P5",
                   "business_req": "负责数据管道建设，需要Spark/Python经验"},
                  token=tok)
    data = d.get("data", {})
    rationale = data.get("rationale", "")
    record("TC-AI-01 AI 输出含 rationale", bool(rationale) and rationale not in ("", [], {}),
           f"rationale_type={type(rationale).__name__}")
    record("TC-AI-02 rationale 非空字符串",
           isinstance(rationale, (str, dict, list)) and str(rationale).strip() != "",
           f"preview={str(rationale)[:50]}")


# ──────────────────── main ────────────────────

def main():
    print("=" * 60)
    print("  HR 招聘 AI 助手 — E2E 功能测试报告")
    print(f"  目标：{BASE}")
    print("  账号：admin / hr / hr_lead / interviewer（真实账号）")
    print("=" * 60)

    t0 = time.time()
    try:
        test_auth()
        tokens = test_menu_rbac()
        job_id = test_job_workflow(tokens)
        resume_id = test_resume_workflow(tokens, job_id)
        iv_id = test_interview_workflow(tokens, resume_id, job_id)
        if resume_id:
            test_status_flow(tokens, resume_id)
        test_analytics(tokens)
        test_dictionary(tokens)
        if resume_id:
            test_compliance(tokens, resume_id)
        test_ai_agent()
    except Exception as e:
        print(f"\n⚠️  测试中止（未捕获异常）：{e}")
        import traceback; traceback.print_exc()

    elapsed = time.time() - t0
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = sum(1 for r in RESULTS if not r["passed"])
    total = len(RESULTS)

    print(f"\n{'='*60}")
    print(f"  测试完成  耗时 {elapsed:.1f}s")
    print(f"  总计 {total} 项  ✅ {passed} PASS  ❌ {failed} FAIL")
    print(f"{'='*60}")

    if failed:
        print("\n失败用例明细：")
        for r in RESULTS:
            if not r["passed"]:
                print(f"  ❌ {r['name']}" + (f" — {r['detail']}" if r['detail'] else ""))

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
