# HR 招聘 AI 助手 测试计划（Test Plan）

| 项 | 内容 |
|---|---|
| 项目名称 | hr-ai-recruitment-copilot |
| 文档版本 | v1.8 |
| 编写角色 | QA Agent |
| 编写日期 | 2026-07-18 |
| 输入依据 | docs/product/PRD.md ｜ docs/architecture/system-design.md ｜ docs/development/mvp-development-plan.md |
| 文档状态 | Draft（与开发并行，测试先行设计，随开发交付滚动更新） |
| 关联文档 | docs/test/test-case.md（测试用例） |

> 修订记录：
> - v1.0（2026-07-18）首次产出，测试先行设计。
> - v1.1（2026-07-18）巡检 #1：开发已交付 T2/T3/T4/T5/T6/T7 模块代码与 pytest 用例；全量 48 passed；补交付状态、R-09（瞬时 flakiness 观测）、QA 补充用例段。`mvp-development-plan.md` 仍缺位。
> - v1.2（2026-07-18）巡检 #2：`mvp-development-plan.md` 已生成 → R-01 解除；新增 Alembic 迁移（init_schema，SQLite 验证通过）；全量 48 passed、ruff clean；发现 `.obs-local/` 测试产物 109 个被暂存拟提交（R-10）；开发者已 `git add` 全部成果物准备提交。
> - v1.4（2026-07-18）巡检 #14：开发提交新 commit `206c196`，T8 数据分析看板正式交付；app 39→42，测试 48→54 passed，ruff clean。R-11 仍未修复，已在 GitHub 建 Issue #1 推动开发修复；R-13/R-10 已解除。
> - v1.5（2026-07-18）巡检 #15：开发连续提交 `fd7990d`（渠道字段 + 真实渠道统计）与 `bfe5ecb`（字典管理 + 批量异步评分 T9），app 42→49，测试 54→76 passed，ruff clean，5 轮复跑稳定。**R-11 已修复**（`require_roles(Role.HR_LEAD, Role.ADMIN)` 已应用到 delete/export 双路由）；R-14 未见再现。T9 正式标记已交付。
> - v1.6（2026-07-18）巡检 #16：开发提交 `3bfbaa8`（fix: 补齐各接口角色门禁 + API 层 RBAC 测试），job draft / interview create&eval / resume upload&analyze&batch-analyze 全部补齐 `require_roles` 门禁；新增 5 个 API 层 RBAC 测试；前端 API 模块（analytics/auth/interview/job/resume）就位；前端页面（Login/Job/Resume/Interview/Analytics）+ 状态管理待提交（6 个 untracked）。测试 81 passed，ruff clean。
> - v1.7（2026-07-18）巡检 #21：开发连续提交 `a4fcd8d`（一键启动脚本 + MockClient 默认响应 + 迁移修复 + seed 数据）+ `69412e5`（动态能力维度 + 岗位模板复用 JD 生成），后端功能增强无新增模块。测试 81 passed，ruff clean。
> - v1.8（2026-07-18）巡检 #22：开发提交 `c7dd423`（Docker Compose 生产部署 + 前端测试体系），新增 `entrypoint.sh`、docker-compose 生产编排、前端 vitest 测试体系（6 测试文件，11 passed + 4 skipped）。后端 81 passed + 前端 11 passed；ruff clean。

---

## 0. 文档依赖说明（重要）

- 本测试计划以 **PRD（功能/非功能/验收标准）**、**system-design（模块/接口/数据模型/AI 架构）** 与 **mvp-development-plan.md（开发进度与已知限制）** 为设计依据。
- ✅ `docs/development/mvp-development-plan.md` 已于巡检 #2 生成（v1.0，Developer Agent），R-01 解除；"迭代–测试准入"映射以 system-design §7 T1–T9 为主线，与开发计划 §1 总体进展对齐。
- 开发计划 §5 已知限制：HuaweiClient 鉴权 token 生成需生产 SDK 完整签名（当前占位）、简历解析仅文本型（OCR 留 P2）、向量匹配未引入、数据分析/批量异步/字典管理为后续阶段。这些限制已纳入本计划范围外项与风险登记。

---

## 一、测试目标

1. **功能符合 PRD**：P0 范围功能（F1.1–F1.4、F2.1–F2.5、F3.1–F3.4、F5.1、F5.4、F5.5）全部可测且通过。
2. **验收标准全覆盖**：PRD §7 的 AC-US-01～AC-US-08 每一条均有对应测试用例并验证（映射见 §8）。
3. **关键流程通过**：JD 生成 → 简历分析 → 面试评价 三段式核心闭环端到端跑通。
4. **AI 质量达标**：AI 输出结构化、可解释、可审计、稳定可复现（详见 §6）。
5. **非功能达标**：性能（JD ≤15s / 简历 ≤20s / 看板 ≤5s）、安全（加密/脱敏/权限）、合规（永久保留/删除审计/导出）均满足 PRD §5。
6. **无阻塞缺陷发布**：上线前 P0/P1 阻塞缺陷为 0（详见 §11 缺陷分级）。

> 测试原则：**简单优先、左移优先、AI 可解释优先**。AI 输出不是"黑盒魔法"，每一条评分/评价/推荐都必须可被结构化校验与人工复核。

---

## 二、测试范围

### 2.1 范围内（In Scope）

| 模块 | 范围 | 优先级 |
|---|---|---|
| AI 职位助手（F1） | JD 生成 / 岗位画像 / 技能要求 / 版本留痕 | P0 |
| AI 简历分析助手（F2） | 上传 / 解析 / 评分 / 优势 / 风险 | P0 |
| AI 面试助手（F3） | 记录录入 / 总结 / 评价 / 推荐 | P0 |
| 系统支撑（F5） | 登录鉴权 / 角色权限 / AI 调用审计 / 数据脱敏 | P0 |
| 简历合规（F5.5+T7） | 永久保留 / 删除审计 / 导出 | P0 |
| AI Agent 基座（T3） | Orchestrator / LLMClient / PromptManager / OutputParser | P0 |
| 招聘数据分析（F4，P1） | 看板指标 / 查询响应 | P1 |
| 横切关注点 | 统一响应封装、异常处理、日志、配置、CI | P0 |

### 2.2 范围外（Out of Scope / 随 P1、P2 推进）

| 项 | 优先级 | 说明 |
|---|---|---|
| F4 招聘数据分析看板 | P1 | 周期/漏斗/渠道/可视化（P1 阶段补测） |
| F1.5 JD 版本编辑、F2.6 批量筛选排序、F3.5 面试问题建议、F5.2 岗位库、F5.3 状态流转 | P1 | 随 P1 迭代纳入 |
| F1.6 / F2.7 / F3.6 / F4.5 | P2 | 远期，本期不测 |
| 移动端 / 原生 App UI | — | 本期为 Web 单页应用 |
| 真实语音转写（F3.6） | P2 | 远期 |
| 生产环境混沌工程与全链路压测 | P1/P2 | 随后阶段 |

> 说明：MVP 期 LLM 真实调用受限于华为云盘古模型版本/端点待确认（system-design §3.4.1 待确认项 a/b）。AI 编排链路先用 `MockClient` 验证结构化输出、审计、降级；真实模型质量评估见 §6.4 与 §6.5。

---

## 三、测试策略

### 3.1 测试金字塔

```
            /\
           /E2E\          少量：核心闭环冒烟（JD→简历→面试）
          /------\
         / 集成 /接口 \     中等：API 契约 + AI 编排链路（MockClient）
        /------------\
       /   单元测试    \    大量：纯函数、解析器、Schema 校验、脱敏、评分规则
      /----------------\
```

- **单元测试（~60%）**：纯逻辑——响应封装、脱敏函数、OutputParser 的 JSON Schema 校验、rationale 抽取、评分区间归一化、权限判定、提示词模板渲染。无外部依赖、毫秒级。
- **接口/集成测试（~30%）**：FastAPI TestClient + 内存 SQLite（沿用现有 `conftest.py`）+ `MockClient` 替身 LLM。覆盖鉴权、各 P0 端点契约、`ai_call_log` 落库、加密/脱敏入库。
- **E2E/端到端（~10%）**：核心闭环冒烟，验证三段式串联、审计可追溯、前端关键页面可渲染。

### 3.2 测试类型映射

| 类型 | 目标 | 工具/框架 | 何时执行 |
|---|---|---|---|
| 静态检查 | 代码风格 / 类型 / 导入 | ruff、mypy（后端）/ ESLint、tsc（前端） | 每次 commit（CI） |
| 单元测试 | 函数级正确性 | pytest + pytest-asyncio + pytest-cov | 每次 commit（CI） |
| 接口测试 | API 契约 + 编排 | pytest + httpx TestClient + MockClient | 每次 commit（CI） |
| 契约测试 | OpenAPI 一致性 | FastAPI `/openapi.json` + schemathesis（P1） | 接口变更时 |
| AI 质量测试 | 结构化/可解释/稳定 | pytest + 固定输入语料 + 黄金集断言 | 提示词/模型变更时 |
| 性能测试 | 响应时延 | locust / httpx 压测脚本 | 迭代末 + 预发 |
| 安全测试 | 鉴权/加密/脱敏/越权 | pytest 安全用例 + 手工核查 | 迭代末 + 预发 |
| 回归测试 | 防止退化 | 全量自动化用例 | 每次 PR + 发布前 |
| 验收测试 | 按 PRD AC 走查 | 人工 + 自动化脚本 | 发布前 |

### 3.3 测试替身策略（关键）

为避免 CI 依赖外网与真实计费，LLM 调用统一走 `LLMClient` 抽象接口（system-design §3.4.1）：

- **单元/接口层**：注入 `MockClient`，按用例预设返回体（成功结构化 / Schema 失败 / 超时 / 服务端错误），验证 Orchestrator 的重试、降级、审计、rationale 抽取。
- **AI 质量层**：使用"固定输入语料 + 黄金期望集"对 `MockClient` 与真实 `HuaweiClient`（预发，小样本）做对照，量化结构化命中率与稳定性。
- **配置切换**：`LLM_PROVIDER=mock` 为测试默认；`LLM_PROVIDER=huawei` 仅在预发联调启用（`backend/app/config.py` 已支持该字段）。

---

## 四、测试环境

| 环境 | 用途 | 数据库 | LLM | 对象存储 | 说明 |
|---|---|---|---|---|---|
| L1 单元/CI | 自动化门禁 | SQLite 内存 | MockClient | Mock | ubuntu-latest，Python 3.11 / Node 20 |
| L2 集成 | 模块联动 | 容器 PostgreSQL + Redis | MockClient | MinIO | 接近生产结构 |
| L3 AI 评测 | AI 质量评测 | 测试库 | HuaweiClient（盘古）/ 可复现 Mock | OBS（脱敏样本） | 真实模型小样本 |
| L4 预发布 | 验收 | 华为云 RDS for PostgreSQL | HuaweiClient | 华为云 OBS（KMS 加密） | 类生产，正式验收 |
| 生产 | 上线 | 华为云 RDS + OBS + DCS | HuaweiClient | OBS（KMS 加密） | 工作时间可用率 ≥99% |

- 配置隔离：测试用 `.env.test`，密钥不入库；AI 测试默认 `LLM_PROVIDER=mock`。
- 环境隔离要求：测试环境 **不得持有真实候选人简历**；预发若需真实语料，须使用脱敏样本并经授权。

---

## 五、测试数据策略

### 5.1 数据来源

| 类型 | 来源 | 用途 | 数量门槛 |
|---|---|---|---|
| 岗位输入语料 | QA 构造覆盖典型/边界/异常的岗位描述 | F1 JD 生成 | ≥5 |
| 简历样本语料 | 合成简历（PDF/Word，含文本型与边界版式） | F2 解析与评分 | ≥20 |
| 面试记录语料 | 合成面试纪要（覆盖推荐/待定/不推荐三种倾向） | F3 评价 | ≥10 |
| 黄金期望集 | 人工标注的"期望结构化输出 + 期望评分区间" | AI 质量断言 | ≥30 |
| 安全/越权数据 | 构造越权 token、注入 payload、超大文件 | 安全测试 | 若干 |

### 5.2 数据管理原则

- 测试数据 **禁止包含真实个人敏感信息**；合成数据中如需演示脱敏，使用明显占位（如 `138****0000`）。
- 小型合成样本纳入 `tests/fixtures/`；大文件用脚本生成，不入库。
- 黄金期望集与提示词版本绑定，提示词变更时同步评审黄金集。

---

## 六、AI 质量验证标准（核心）

> 本项目 AI 输出是核心交付物，须以"工程化质量"对待，而非仅做主观验收。以下标准既是测试断言依据，也是 AI 模块的完成标准。

### 6.1 结构化输出合规性（Structured Output Conformance）

| 标准 | 验证方法 | 通过门槛 |
|---|---|---|
| 所有 AI 输出符合预定义 JSON Schema | OutputParser 对返回体做 Schema 校验，断言通过 | ≥99% 用例 Schema 合法 |
| 必填字段齐全 | JD：`jd/job_profile/skill_requirements/rationale`；简历：`match_score/advantages/risks/rationale`；面试：`summary/capability_eval/recommendation/rationale` | 缺一即判失败 |
| 评分类数值在约定区间 | `match_score ∈ [0,100]`；`recommendation ∈ {推荐,待定,不推荐}` | 100% 越界即失败 |
| Schema 校验失败可降级/重试 | 触发 OutputParser 重试或降级路径，最终给出明确错误而非崩溃 | 降级链路可验证 |

### 6.2 可解释性（Explainability）

| 标准 | 验证方法 |
|---|---|
| 每次 AI 输出必含 `rationale` 字段 | 断言 `rationale` 非空且为结构化对象 |
| 评分类输出含命中/缺失明细 | 简历评分 `rationale` 含命中技能项与缺失技能项；面试评价 `rationale` 含各能力维度依据 |
| rationale 与结论一致 | 抽样人工核查：评分高者命中项显著多于缺失项；推荐结论与能力评价自洽 |
| 无"空依据"或模板化敷衍 | 断言 rationale 不为空字符串、不含占位模板字面量 |

### 6.3 可审计性（Auditability）

| 标准 | 验证方法 |
|---|---|
| 每次 LLM 调用写入 `ai_call_log` | 调用后查库断言记录存在 |
| 审计字段完整 | `agent_type/model/prompt_version/input_digest/output_digest/latency_ms/status/operator_id/created_at` 均非空（敏感摘要脱敏） |
| 审计只增不删 | 无删除/更新接口；尝试调用应被拒绝 |
| 输入摘要脱敏 | `input_digest` 不含明文身份证/手机号；简历原文不入日志 |
| 可与业务结果关联 | `resume_match_result.ai_call_log_id`、`interview_eval.ai_call_log_id` 外键存在 |

### 6.4 稳定性与一致性（Stability / Consistency）

| 标准 | 验证方法 | 门槛 |
|---|---|---|
| 同一输入多次调用评分稳定 | 固定简历+岗位，N 次评分，计算标准差 | 真实模型 σ ≤ 8 分；Mock 固定返回 |
| 关键结论一致 | 评分档位/推荐结论在容差内一致 | 一致率 ≥ 90% |
| 提示词版本可追溯 | 同一提示词版本下结果可复现；版本变更触发回归 | prompt_version 落库可查 |
| 确定性回放 | MockClient 固定输入→固定输出 | 100% 可复现 |
| 批量一致 | 批量中相同简历评分一致 | 重复样本评分一致 |

### 6.5 内容质量底线（Grounding / 基础正确性）

| 标准 | 验证方法 | 门槛 |
|---|---|---|
| JD 字段完整率 | 输出三部分字段齐全 | ≥ 95% |
| 不捏造岗位要求 | JD 技能要求与输入业务要求/岗位画像可对应 | 人工/规则核查 |
| 评分有据 | 命中项可在 `parsed_data` 中查到 | 100% |
| 面试评价不离题 | `capability_eval` 维度对齐 `competency_template` | 维度覆盖 100% |
| 推荐建议与人工判定一致率 | 黄金集对照 | ≥ 80% |
| 公平性底线 | 合成简历仅改变性别/无关属性时，评分不应显著偏移 | 偏差检测用例通过 |

### 6.6 成本与时延

| 标准 | 验证方法 |
|---|---|
| 单次 JD ≤15s | 接口测试计时断言 |
| 单份简历解析+评分 ≤20s | 接口测试计时断言 |
| 看板查询 ≤5s | 性能测试（P1） |
| LLM 调用重试有限（≤3）、超时 30s | MockClient 注入超时/错误，断言重试次数与最终失败行为 |
| token/cost 落库可追踪 | `ai_call_log` 含 usage 字段（或等价） |

### 6.7 安全与脱敏

- 送入 LLM 的文本不得包含明文身份证号 / 手机号 / 住址（脱敏检查通过率 100%）。
- `ai_call_log` 不记录简历明文，仅记录摘要/哈希。

---

## 七、接口测试方案

### 7.1 接口契约清单

> 依据 system-design §5。统一响应：`{ "code": 0, "message": "ok", "data": <payload> }`，错误 `code != 0`。

| 方法 + 路径 | 说明 | 鉴权 | 优先级 |
|---|---|---|---|
| GET /api/health | 探活（已实现） | 否 | P0 |
| POST /api/auth/login | 登录颁发 JWT | 否 | P0 |
| POST /api/auth/refresh | 刷新令牌 | refresh | P0 |
| POST /api/jobs/draft | AI 生成 JD | HR+ | P0 |
| GET /api/jobs | 岗位列表 | HR+ | P0 |
| GET/PUT /api/jobs/{id} | 查询/编辑岗位 | HR+ | P0/P1 |
| POST /api/resumes/upload | 上传简历（加密存 OBS） | HR+ | P0 |
| POST /api/resumes/{id}/analyze | 简历匹配评分 | HR+ | P0 |
| GET /api/resumes | 简历列表（按评分排序） | HR+ | P0/P1 |
| DELETE /api/resumes/{id} | 删除简历（人工触发+审计） | HR_LEAD/ADMIN | P0 |
| GET /api/resumes/{id}/export | 导出（可携带） | HR_LEAD/ADMIN | P0 |
| POST /api/interviews | 录入面试记录 | INTERVIEWER+ | P0 |
| POST /api/interviews/{id}/evaluate | 面试评价 | INTERVIEWER+ | P0 |
| GET /api/audit/ai-calls | AI 调用审计查询 | ADMIN | P0 |
| GET /api/analytics/overview | 招聘看板 | HR_LEAD | P1 |

> 角色简称：HR=招聘专员、HR_LEAD=负责人、INTERVIEWER=面试官、ADMIN=管理员；"+"表示该角色及以上。

### 7.2 接口测试维度

每个接口验证（详见 test-case.md）：

1. **正常路径**：合法输入 → 200 + `code=0` + 数据结构正确。
2. **鉴权**：无 token / 过期 token / 错误角色 → 401/403。
3. **入参校验**：缺字段、类型错误、超长、非法枚举 → 422 / `code != 0`。
4. **业务异常**：资源不存在 404、状态非法 409。
5. **AI 编排**：`MockClient` 注入成功/Schema 失败/超时/服务端错误，验证重试与降级。
6. **审计落库**：AI 类接口调用后 `ai_call_log` 有记录且字段完整。
7. **安全**：越权访问他人简历、注入 payload、超大文件 → 拒绝。
8. **幂等/并发**：重复提交、并发评分结果一致性。

### 7.3 统一响应断言

所有接口返回 `{ code, message, data }`，断言 `code=0` 为成功；非 0 视为业务失败。错误码集中定义在 `backend/app/common/response.py`，新增错误码需登记。

### 7.4 工具与执行

- 后端接口测试：`pytest + TestClient`，置于 `backend/tests/`（沿用 `conftest.py` 的内存 SQLite + `get_db` 覆盖）。
- 契约基线：FastAPI 自动生成 `/openapi.json`；前端 `src/api/client.ts` 类型与之对齐。
- 前端：`api/client.ts` 拦截器解包统一结构。

---

## 八、验收标准映射（AC ↔ TC）

> 将 PRD §7 验收标准拆解为可测试条目，每条映射到 test-case.md 用例编号。

### AC-US-01（JD 生成）

| # | 验收条目 | 测试方法 | 用例编号 |
|---|---|---|---|
| 1 | 15s 内返回结果 | 接口计时断言 | TC-304 |
| 2 | 输出含 JD/岗位画像/技能要求且字段完整 | Schema 校验 | TC-301、TC-302 |
| 3 | JD 可编辑并保存版本 | 接口+数据校验 | TC-306（P1） |
| 4 | 附带依据说明 | rationale 断言 | TC-303 |

### AC-US-02（简历分析）

| # | 验收条目 | 测试方法 | 用例编号 |
|---|---|---|---|
| 1 | 支持 PDF/Word 导入并解析 | 上传+解析断言 | TC-401、TC-402、TC-405 |
| 2 | 输出 0–100 评分+优势+风险 | Schema+区间断言 | TC-406、TC-407 |
| 3 | 评分附依据（命中/缺失） | rationale 断言 | TC-408 |
| 4 | 批量后按评分排序 | 列表排序断言 | TC-411（P1） |

### AC-US-03（面试助手）

| # | 验收条目 | 测试方法 | 用例编号 |
|---|---|---|---|
| 1 | 生成总结+能力评价+推荐 | Schema 断言 | TC-502 |
| 2 | 推荐为三选一并附依据 | 枚举+rationale 断言 | TC-503、TC-505 |
| 3 | 评价基于统一能力维度模板 | 维度对齐断言 | TC-504 |

### AC-US-04（数据分析，P1）

| # | 验收条目 | 测试方法 | 用例编号 |
|---|---|---|---|
| 1 | ≥3 项指标 | 看板接口断言 | TC-601 |
| 2 | 查询 ≤5s | 性能断言 | TC-603 |
| 3 | 按时间区间筛选 | 参数校验 | TC-602 |

### AC-US-06（权限与审计）

| # | 验收条目 | 测试方法 | 用例编号 |
|---|---|---|---|
| 1 | 角色仅能访问授权功能 | 越权用例 | TC-103、TC-106、TC-107 |
| 2 | 所有 AI 调用留存可审计日志 | 审计落库断言 | TC-208、TC-209 |
| 3 | 简历等敏感数据加密存储 | 加密/脱敏断言 | TC-404、TC-706、TC-410、TC-906 |

### AC-US-08（合规：删除/导出，P0）

| # | 验收条目 | 测试方法 | 用例编号 |
|---|---|---|---|
| 1 | 简历永久保留、无自动清理 | 无定时清理任务断言 | TC-701 |
| 2 | 删除为人工触发并留审计 | 删除+审计断言 | TC-702、TC-703 |
| 3 | 支持导出 | 导出接口断言 | TC-704、TC-705 |

### 发布门禁（Release Gate）

- P0 用例 100% 执行且通过率 100%；P1 用例 ≥95%；
- 无 P0/P1 阻塞缺陷；
- 性能、安全、合规专项全部通过；
- AI 质量六维标准（§6.1–6.6）全部达标或经评审可降级。

---

## 九、测试准入节奏（对齐 system-design T1–T9）

> 由于 `mvp-development-plan.md` 缺位，暂以 system-design §7 任务为代理。开发计划补全后滚动对齐。

| 阶段 | 开发任务 | 测试准入 | 交付状态（v1.1 巡检） |
|---|---|---|---|
| T1 工程脚手架 | 前后端/CI/Docker | 已就绪，回归 health | ✅ test_health.py 2 passed + vitest 前端 11 passed（巡检 #22） |
| T2 用户/角色/JWT | 登录与角色可见性 | 单元+接口：鉴权、RBAC、token | ✅ test_auth.py 8 + test_authz.py 2 passed |
| T3 AI Agent 基座 | Orchestrator/LLMClient/OutputParser + 审计 | 单元+接口：编排、Schema、重试降级、审计 | ✅ test_ai_agent.py 9 passed |
| T4 JD 生成 E2E | ≤15s、含依据 | 接口+E2E+AI 质量 | ✅ test_job.py 7 passed |
| T5 简历分析 E2E | ≤20s、含依据、加密 | 接口+E2E+AI 质量+安全 | ✅ test_resume.py 12 passed |
| T6 面试评价 E2E | 总结/评价/推荐、含依据 | 接口+E2E+AI 质量 | ✅ test_interview.py 8 passed |
| T7 简历合规 | 永久保留+删除/导出审计 | 合规专项 | ✅ 含于 test_resume.py（软删/重复删除冲突/导出） |
| T8 数据分析（P1） | 看板 ≥3 指标、≤5s | 接口+性能 | ✅ 已交付（test_analytics.py 6 passed；含空数据/漏斗/时间筛选/RBAC 403/HR_LEAD 200/性能 ≤5s） |
| T9 批量/字典（P1） | 批量筛选排序、岗位库 | 接口 | ✅ 已交付（test_t9.py 12 passed；含字典 CRUD + 技能唯一约束 + 默认模板独占 + RBAC 门禁 + 批量异步 eager + API） |
| 集成/验收 | 三段闭环 | E2E+AC 走查 | ⏳ 待补 E2E 串联用例 |

> 全量后端自动化：**48 passed**（pytest -q，含 5 次复跑稳定）。详见 §14 巡检记录。

---

## 十、测试进度与里程碑

| 里程碑 | 内容 | 状态 |
|---|---|---|
| M1 测试设计 | 测试计划+用例+AI 质量标准+接口方案+验收标准 | 进行中（本期完成） |
| M2 脚手架验证 | T1 脚手架冒烟（health/CI） | 已具备 |
| M3 单元/接口测试 | T2–T7 模块随开发交付对应测试 | 待开发交付 |
| M4 集成测试 | 三助手闭环 | 待开发交付 |
| M5 AI 评测 | 评测集执行 | 待评测集就绪 |
| M6 验收测试 | AC 走查+报告 | 发布前 |

---

## 十一、缺陷管理

### 11.1 缺陷分级

| 级别 | 定义 | 处置时限 |
|---|---|---|
| P0 阻塞 | 核心功能不可用 / 数据丢失 / 安全漏洞 / AI 输出无依据 | 当日内修复，阻塞发布 |
| P1 严重 | 主功能受损但有绕过 / 性能不达标 / 审计缺失 | 迭代内修复 |
| P2 一般 | 次要功能问题 / 体验问题 | 下迭代修复 |
| P3 轻微 | 文案/样式/非功能性小瑕疵 | 择机修复 |

### 11.2 缺陷流程

1. 发现缺陷 → 创建 GitHub Issue（type=Bug，按 `.github/ISSUE_TEMPLATE/bug.md`，含复现步骤/期望/实际/环境/截图）。
2. QA 复核 → 标定级别与归属。
3. Developer 修复 → PR 关联 Issue。
4. QA 回归验证通过 → 关闭 Issue。
5. **禁止**：直接改代码绕过流程、删除失败用例、隐瞒问题（enterprise.md / qa-agent.md）。

---

## 十二、风险与依赖

| 编号 | 风险 | 影响 | 概率 | 缓解 |
|---|---|---|---|---|
| ~~R-01~~ | ~~`mvp-development-plan.md` 缺位~~ | — | — | ✅ 已解除（巡检 #2：开发计划 v1.0 已生成） |
| R-02 | 华为云盘古具体模型版本/端点未定；HuaweiClient 鉴权 token 为占位（mvp-plan §5.1） | 真实模型质量无法提前验证 | 高 | MVP 用 MockClient 保证编排正确；预发小样本评估，预留接入点在 HuaweiClient |
| R-03 | 真实 LLM 输出非确定性，评分稳定性难保证 | AI 质量门槛难达标 | 中 | 固定语料黄金集 + 标准差门槛；提示词约束 + 结构化输出 + 重试 |
| R-04 | 简历解析对复杂版式/扫描件能力不足（mvp-plan §5.2 明确仅文本型） | F2.2 解析失败率升高 | 中 | MVP 聚焦文本型 PDF/Word；扫描件 OCR 明确为按需/远期 |
| R-05 | 测试环境使用真实简历有合规风险 | 合规违规 | 低 | 一律合成样本；预发须授权+脱敏 |
| R-06 | JSONB 等 PG 特性在 SQLite 测试环境行为差异；Alembic 迁移已用 with_variant 兼容 | 测试与生产不一致 | 中 | 用 SQLAlchemy 通用类型；Alembic 迁移在 SQLite 验证通过；关键路径在预发 PG 复跑 |
| R-07 | 提示词版本与黄金期望集漂移 | AI 回归失效 | 中 | 提示词变更强制评审黄金集并升版本号 |
| R-08 | 永久保留的存储与备份成本（system-design 待确认 c） | 长期成本 | 中 | P1 评估 OBS 生命周期与 RDS 备份策略 |
| R-09 | 简历相关用例偶现 flakiness（巡检 #1 首轮 5 failed，20+ 次复跑 0 failed） | 测试可靠性 | 低 | 持续观测；巡检 #2 全量 48 passed 稳定；下轮若再现则定位根因并建 Issue |
| R-10 | ~~`.obs-local/resumes/*` 测试产物被暂存拟提交~~ | — | — | ✅ 已解除（巡检 #3：开发者移出暂存区并补入 `backend/.gitignore`，暂存区 0 个 obs-local 文件）。⚠️ 残留：`backend/.gitignore` 该改动本身仍 unstaged，建议 `git add backend/.gitignore` |
| R-11 | ~~`DELETE /api/resumes/{id}` 与导出仅校验登录、无角色门禁~~ | — | — | ✅ 已修复（巡检 #15：commit `bfe5ecb` 中 `resume.py:52/58` 已应用 `require_roles(Role.HR_LEAD, Role.ADMIN)`）；需补 TC-908 自动化回归用例 |
| R-12 | Alembic init_schema 中 `user` 表的 `role` 为 String 而非 FK/Enum，`deleted` 用 Integer 软删 | 数据完整性弱约束 | 低 | 已知设计；后续可加 Check 约束；非阻塞 |
| R-13 | docs/test 文档 staged 版本滞后于工作区 | 提交内容不完整 | 中 | ✅ 已解除（巡检 #12：开发者已 git add 同步 v1.3） |
| R-14 | test_analytics 复跑偶现 56 passed（预期 54，多 2 个）；疑为测试隔离问题 | 测试可靠性 | 低 | 巡检 #15 未见再现（76 passed 6 轮稳定）；解除观测 |

---

## 十三、完成标准（QA Agent 自检）

- ✅ 测试计划完成（本文档）
- ✅ 测试用例完成（docs/test/test-case.md），覆盖 P0 全部功能与验收标准
- ✅ AI 质量验证标准定义完成（§6）
- ✅ 接口测试方案定义完成（§7）
- ✅ 验收标准映射完成（§8）
- 🟡 测试执行：T1–T7 已交付并 48 passed；T8/T9 未交付；E2E 串联、AI 黄金集评测待补
- ⏳ 测试报告（docs/test/test-report.md，迭代末产出）
- ⏳ 发布建议（迭代末明确）

---

## 十四、巡检记录（每 20 分钟，随开发进展滚动）

| 时间 | 基准/状态 | 发现 | 测试结果 | 处置 |
|---|---|---|---|---|
| 巡检 #1 2026-07-18 | HEAD=41979ef（脚手架期），mvp-plan 缺 | 开发已大幅推进：auth/job/resume/interview + ai 基座 + 模型/服务/路由/Schema + test_auth/authz/ai_agent/job/resume/interview | pytest 全量 **48 passed**；首轮曾现 5 failed，后续 20+ 次复跑 0 failed，判定瞬时 flakiness | 升 v1.1；登记 R-09；未建 Issue（未能稳定复现） |
| 巡检 #15 2026-07-18 | HEAD `aa4099f`（三连 commit：fd7990d + bfe5ecb + aa4099f） | 渠道字段+真实渠道统计；字典管理（PositionTemplate/SkillDict/CompetencyTemplate 三表+CRUD+RBAC）；批量异步评分（Celery+eager 测）；**R-11 已修复**（`aa4099f` fix: DELETE/export 补齐 `require_roles(Role.HR_LEAD, Role.ADMIN)`） | ruff clean；pytest **76 passed**（8 轮复跑全部稳定） | 升 v1.5；T9 已交付；R-11 已修复 + GitHub Issue #1 已关闭；R-14 解除；TC-908 自动化回归待补 |

> 指纹比对基准更新：HEAD=`aa4099f`，app 49 .py（8 api + 7 service），测试 76 passed（9 个 test 文件），ruff clean。T1–T9 全部交付：仅剩 TC-801 E2E 闭环串联、TC-908/TC-705 自动化回归、真实 HuaweiClient 预发联调。

> 🔴 待人工确认项（巡检 #3）：
> 1. **R-13**：`docs/test/test-plan.md` 与 `test-case.md` 的 staged 版本滞后于工作区（staged: v1.1/v1.0；工作区: v1.3/v1.3）。开发者提交前需 `git add docs/test/` 同步，否则提交的测试文档为旧版本。
> 2. **R-10 残留**：`backend/.gitignore` 的 `.obs-local/` 补充改动仍 unstaged，建议一并 `git add`。
> 3. **R-11**：简历删除/导出接口仍缺角色门禁，与 §7.1 约定（限 HR_LEAD/ADMIN）不符，建议开发补 `require_roles`。
> 4. 本轮 app/test 代码无新增，故未触发新增用例落地；R-09 瞬时 flakiness 未再现。

---

> **完成标准自检**：✅ 范围明确 ｜ ✅ 策略明确 ｜ ✅ AI 质量标准可测 ｜ ✅ 接口方案可执行 ｜ ✅ 验收标准可追溯 ｜ ✅ 发布门禁明确
