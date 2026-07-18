# MVP 开发进度说明

| 项 | 内容 |
|---|---|
| 项目 | hr-ai-recruitment-copilot |
| 文档版本 | v1.0 |
| 编写角色 | Developer Agent |
| 编写日期 | 2026-07-18 |
| 依据 | docs/product/PRD.md、docs/architecture/system-design.md |
| 分支 | feature/001-project-scaffold |

> 说明：本文记录 MVP 开发阶段各技术任务的实现范围、关键决策与验证结果，作为 PR 说明与可追踪依据。对应 system-design 第七章任务拆解 T1–T7。

---

## 一、总体进展

| Task | 内容 | 状态 | 测试 |
|---|---|---|---|
| T1 | 工程脚手架（前后端 + CI + Docker） | ✅ 完成 | 冒烟通过 |
| T2 | 用户/角色/权限 + JWT 鉴权 | ✅ 完成 | 7 用例通过 |
| T3 | AI Agent 基座 + 华为云盘古 LLMClient | ✅ 完成 | 8 用例通过 |
| T4 | AI 职位助手（JD 生成）端到端 | ✅ 完成 | 7 用例通过 |
| T5 | AI 简历分析助手（上传/解析/评分） | ✅ 完成 | 13 用例通过 |
| T6 | AI 面试助手（评价/推荐） | ✅ 完成 | 8 用例通过 |
| T7 | 简历合规（永久保留 + 删除/导出审计） | ✅ 完成 | 含于 T5 |

**自动化测试：48 passed，ruff lint：All checks passed。**

---

## 二、技术栈落地（已人工确认）

- 后端：Python 3.11 + FastAPI + SQLAlchemy 2.x + Alembic + JWT（bcrypt 4.x）
- 数据：PostgreSQL（生产华为云 RDS），SQLite 兼容用于测试
- AI：统一 LLMClient，`HuaweiClient`（华为云盘古）+ `MockClient`（测试/CI）
- 对象存储：`ObjectStorage` 抽象，`LocalObjectStorage` 兜底，生产注入 OBSClient
- 部署：Docker + docker-compose + GitHub Actions
- 简历永久保留（`retention_until` 留空，无自动清理），删除为人工显式 + 软删除留痕

---

## 三、模块与接口清单

### 后端目录结构
```
backend/app/
├── main.py                 # FastAPI 入口
├── config.py               # 配置（环境变量）
├── db.py                    # SQLAlchemy 引擎与会话
├── api/                     # 路由：health/auth/job/resume/interview
├── models/                  # ORM：user/ai_call_log/job/resume/interview
├── schemas/                 # Pydantic 入参/出参
├── services/                # 业务服务层
├── ai/                      # Agent 基座：orchestrator/llm_client/prompt_manager/output_parser
└── common/                  # response/auth/security/redact/storage/logging
```

### 接口清单（已实现）
| 接口 | 方法 | 说明 |
|---|---|---|
| /api/health | GET | 探活 |
| /api/auth/login | POST | 登录 |
| /api/auth/refresh | POST | 刷新令牌 |
| /api/auth/me | GET | 当前用户 |
| /api/jobs/draft | POST | AI 生成 JD |
| /api/jobs/{id} | GET/PUT | 查询/编辑岗位 |
| /api/jobs/{id}/versions | GET | JD 版本列表 |
| /api/resumes/upload | POST | 上传简历 |
| /api/resumes/{id}/analyze | POST | 简历匹配评分 |
| /api/resumes | GET | 简历列表（可按评分排序） |
| /api/resumes/{id} | DELETE | 删除简历（审计） |
| /api/resumes/{id}/export | GET | 导出简历 |
| /api/interviews | POST | 录入面试记录 |
| /api/interviews/{id}/evaluate | POST | 面试评价 |

---

## 四、AI 可解释与可审计实现

- 所有 AI 输出经 `OutputParser` 解析并强制 `require_rationale`（缺依据即缺陷，返回 502）；
- 每次 LLM 调用经 `AgentOrchestrator` 写 `ai_call_log`（仅存摘要/哈希，不含明文）；
- 简历送入 LLM 前经 `mask_sensitive` 脱敏（身份证/手机/邮箱）；
- 评分类输出附带命中/缺失项；推荐建议限定「推荐/待定/不推荐」；
- 能力评价强制覆盖能力模板全部维度。

---

## 五、已知限制与后续

1. `HuaweiClient` 的鉴权 token 生成需在生产用华为云 SDK 完整签名（当前为占位，接入点已隔离）；
2. 简历解析 MVP 仅处理文本型 PDF/Word/txt，复杂版式 OCR 留待 P2；
3. 向量语义匹配（pgvector）未引入，MVP 用结构化技能 + LLM 推理；
4. 数据分析看板（F4，P1）、批量异步（Celery）、字典管理为后续阶段；
5. `docs/development/mvp-development-plan.md` 仓库暂缺，QA 已在 test-plan 中标注待回溯。

---

## 六、验证命令

```bash
cd backend
pip install -e ".[dev]"
ruff check app tests        # All checks passed
pytest -q                   # 48 passed
# 数据库迁移（生产 PG）
alembic upgrade head
```
