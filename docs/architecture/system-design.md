# HR 招聘 AI 助手 系统技术设计方案

| 项 | 内容 |
|---|---|
| 项目名称 | hr-ai-recruitment-copilot |
| 文档版本 | v1.0 |
| 编写角色 | Architect Agent |
| 编写日期 | 2026-07-18 |
| 输入依据 | docs/product/PRD.md |
| 文档状态 | Draft（待技术评审） |

> 本方案遵循设计原则：简单优先、可扩展、可维护、安全。不引入无必要复杂组件，MVP 阶段以单体为主、预留向可扩展架构演进的空间。

---

## 一、系统总体架构设计

### 1.1 架构目标

- 与 PRD 一致：覆盖 JD 生成 / 简历分析 / 面试助手 / 数据分析（P1）/ 系统支撑核心闭环；
- AI 输出可解释、可审计（满足企业规则）；
- 简历等敏感数据加密存储、可删除/导出（合规）；
- 三个 AI 助手以可插拔模块形态存在，便于后续新增 AI 能力。

### 1.2 分层架构

```
┌──────────────────────────────────────────────────────────────┐
│                       前端层 (Frontend)                       │
│   Web 单页应用：JD生成 / 简历分析 / 面试助手 / 看板 / 管理后台   │
└──────────────────────────────────────────────────────────────┘
                              │ HTTPS
┌──────────────────────────────────────────────────────────────┐
│                     网关层 (API Gateway)                       │
│           鉴权 / 限流 / 路由 / 请求日志 / 审计入口               │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                     应用服务层 (Application)                   │
│  JobService│ResumeService│InterviewService│AnalyticsService   │
│  UserService│AuditService│DictionaryService                   │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                     AI Agent 层 (AI)                          │
│   JobAgent │ ResumeAgent │ InterviewAgent │ AgentOrchestrator  │
│   PromptManager │ LLMClient │ ResumeParser                    │
└──────────────────────────────────────────────────────────────┘
        │                          │
┌───────────────────┐   ┌───────────────────────────────────────┐
│   存储层 (Storage)  │   │            外部能力 (External)          │
│ 关系库 / 对象存储   │   │   LLM API / 向量库 / OCR-解析服务       │
│ 缓存 / 审计日志     │   │                                       │
└───────────────────┘   └───────────────────────────────────────┘
```

### 1.3 部署形态（MVP）

- 单体应用部署（前端 + 后端同仓或相邻部署），降低运维复杂度；
- 后端按「模块化单体（Modular Monolith）」组织，模块边界清晰，为后续拆分微服务预留；
- 部署依赖：应用进程、关系数据库、对象存储（简历文件）、缓存（可选）、LLM API（外部）。

### 1.4 模块划分

| 模块 | 职责 | 对应 PRD |
|---|---|---|
| `job` | 岗位与 JD 管理、JD 生成编排 | F1 |
| `resume` | 简历导入、解析、评分、筛选 | F2 |
| `interview` | 面试记录、总结、评价、推荐 | F3 |
| `analytics` | 招聘周期/转化率/渠道分析（P1） | F4 |
| `ai-agent` | AI Agent 编排、提示词管理、LLM 调用、解析 | F1/F2/F3 底座 |
| `user` | 用户、角色、权限 | F5.1 |
| `audit` | AI 调用与关键操作审计日志 | F5.4 |
| `dictionary` | 岗位库、技能字典、能力维度模板（P1） | F5.2 |
| `common` | 通用能力：加解密、文件、异常、响应封装 | — |

---

## 二、AI Agent 架构设计

### 2.1 设计思路

- 每个 AI 助手对应一个 **Agent**，封装「输入预处理 → 提示词构建 → LLM 调用 → 结构化输出解析 → 依据沉淀」；
- 由 **AgentOrchestrator** 统一调度，处理鉴权上下文、审计埋点、限流与重试、结果落库；
- **PromptManager** 集中管理提示词模板（版本化），满足「可解释、可追溯」；
- 输出强制 **结构化（JSON Schema 约束）**，并附带 `rationale`（依据），用于可解释性与审计。

### 2.2 Agent 组件结构

```
                ┌─────────────────────────────────────┐
                │          AgentOrchestrator           │
                │ 鉴权上下文/审计/限流/重试/结果落库     │
                └──────────────┬──────────────────────┘
                               │
   ┌───────────────┬───────────┴───────────┬───────────────┐
   ▼               ▼                       ▼               ▼
┌─────────┐  ┌──────────┐          ┌────────────┐  ┌──────────┐
│JobAgent │  │ResumeAgent│          │InterviewAgent│  │ (可扩展) │
└────┬────┘  └─────┬────┘          └──────┬─────┘  └──────────┘
     │             │                      │
     ▼             ▼                      ▼
┌──────────────────────────────────────────────────┐
│ PromptManager (模板版本化)  │  LLMClient (统一调用) │
└──────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────┐
│ OutputParser (JSON Schema 校验 + rationale 抽取)  │
└──────────────────────────────────────────────────┘
```

### 2.3 各 Agent 职责

| Agent | 输入 | 处理 | 输出（结构化 + 依据） |
|---|---|---|---|
| JobAgent | 岗位名称、等级、业务要求 | 岗位画像检索 → 提示词构建 → LLM | `{jd, job_profile, skill_requirements, rationale}` |
| ResumeAgent | 简历文件 + 目标岗位 ID | 解析简历 → 与岗位画像匹配 → 评分推理 | `{match_score, advantages, risks, rationale}` |
| InterviewAgent | 面试记录 + 岗位/能力模板 | 能力维度对齐 → LLM 总结评价 | `{summary, capability_eval, recommendation, rationale}` |

### 2.4 关键策略

- **可解释性**：所有 AI 输出携带 `rationale` 字段；评分类输出同时返回命中/缺失项明细。
- **可审计**：每次 LLM 调用经由 Orchestrator 写入 `ai_call_log`（操作人、输入摘要、输出摘要、耗时、模型、提示词版本）。
- **结构化输出**：使用 LLM 的结构化输出能力（JSON Schema / function calling），`OutputParser` 校验失败则重试或降级。
- **降级与重试**：LLM 调用失败按策略重试（有限次），超时/失败返回明确错误并记录，避免阻塞用户。
- **成本控制**：长文本（简历、面试记录）先经摘要/分段处理再送 LLM；提示词模板集中维护减少冗余。
- **隔离**：用户敏感数据进入 LLM 前按合规要求脱敏（如身份证号、手机号脱敏）；简历原文不随意外泄至日志。

---

## 三、技术选型建议

> 选型遵循「简单优先」：MVP 优先成熟、生态完善、团队可承接的栈；标 ⭐ 为 MVP 推荐。

### 3.1 前端

| 维度 | MVP 推荐 ⭐ | 理由 |
|---|---|---|
| 框架 | React + TypeScript | 生态成熟，组件丰富，类型安全 |
| 构建 | Vite | 启动快、配置简单 |
| UI | Ant Design | 企业中后台组件齐全，适配招聘管理类界面 |
| 状态/请求 | React Query + Zustand | 服务端状态与本地状态分离，简洁 |
| 图表（P1） | ECharts | 看板可视化能力强 |

### 3.2 后端

| 维度 | MVP 推荐 ⭐ | 理由 |
|---|---|---|
| 语言/框架 | Python + FastAPI | 异步性能好，AI/LLM 生态契合，便于集成解析与模型调用 |
| ORM | SQLAlchemy 2.x + Alembic | 主流、迁移可控 |
| API 规范 | REST + OpenAPI | FastAPI 原生支持，前端易对接 |
| 鉴权 | JWT (访问令牌 + 刷新令牌) | 无状态、易扩展 |
| 任务队列（P1） | Celery + Redis | 简历批量、异步 LLM、定时统计离线处理 |

> 备选：若团队更偏 Java 生态，后端可换 Spring Boot，AI 层通过独立 Python 服务承接（HTTP 调用），保持职责分离。

### 3.3 数据与存储

| 维度 | MVP 推荐 ⭐ | 理由 |
|---|---|---|
| 关系数据库 | PostgreSQL（华为云 RDS for PostgreSQL） | 支持丰富类型、JSONB 利于半结构化存储 |
| 对象存储 | 华为云 OBS | 存储简历原文件（加密 + KMS 加密） |
| 缓存 | Redis（华为云 DCS） | 会话、限流、热点字典 |
| 向量库（P1/按需） | pgvector（复用 PG）或华为云向量检索 | 简历与岗位语义匹配；MVP 可先用结构化匹配，向量匹配延后 |
| 全文检索（P2） | Elasticsearch | 简历全文检索；MVP 不引入 |

### 3.4 AI 能力

| 维度 | MVP 推荐 ⭐ | 理由 |
|---|---|---|
| LLM | 主用华为云盘古大模型 + 统一 LLMClient 适配层（可切换 Claude/OpenAI） | 部署同在华为云，国内合规与延迟更优；适配层保留切换能力 |
| 简历解析 | 先 LLM 抽取 + 轻量解析组件；复杂版式按需 OCR | MVP 优先解析文本型 PDF/Word |
| 模型接入封装 | 统一 `LLMClient` 接口 | 屏蔽不同模型差异，便于切换/多模型 |
| 提示词管理 | 版本化模板（落库 + 文件兜底） | 可审计、可回滚 |

### 3.4.1 LLM 接入具体方案（华为云盘古）

**接入路径**：通过华为云 ModelArts / 盘古大模型推理 API（或预测中心 PredictCenter）调用，鉴权使用华为云 IAM AK/SK，区域与 OBS/RDS 同区以降低延迟与跨区流量。

**LLMClient 适配层设计**：
```
业务模块(JobAgent/ResumeAgent/InterviewAgent)
            │  统一调用接口
            ▼
       LLMClient (抽象接口)
   ┌────────┼─────────┬─────────────┐
   ▼        ▼         ▼             ▼
HuaweiClient  ClaudeClient  OpenAIClient  (MockClient 用于测试)
```
- 抽象接口：`chat(messages, schema?, model?, **opts) -> {content, parsed, usage, latency}`
- 主实现 `HuaweiClient` 封装盘古 API 的请求/鉴权/重试/限流/计费埋点；
- 通过环境变量 `LLM_PROVIDER=huawei` 切换，无需改业务代码；
- `MockClient` 用于单元测试与 CI，避免真实消耗与外网依赖。

**结构化输出**：盘古模型支持结构化输出时优先使用；若不支持则采用「系统约束 + JSON 解析 + 校验重试」兜底，由 `OutputParser` 统一校验。

**密钥管理**：AK/SK 不入库，通过华为云凭据管理服务（DEW/KMS）托管，应用启动时拉取注入；本地开发用 `.env`（加入 `.gitignore`）。

**容错与成本**：
- 重试策略：指数退避、有限次（如 3 次），超时 30s；
- 长文本（简历/面试记录）先分段或摘要再送入；
- 每次调用记录 `model / tokens / latency / cost` 到 `ai_call_log` 用于成本与质量追踪。

**可选增强**：后续可接入盘古行业模型（如招聘/简历领域微调版本）以提升简历与岗位匹配质量，接入点仍在 `LLMClient`，对上层透明。

### 3.5 部署与工程

| 维度 | MVP 推荐 ⭐ | 理由 |
|---|---|---|
| 容器化 | Docker + docker-compose | 本地与单机部署一致 |
| 反向代理 | Nginx | 静态资源 + HTTPS + 简单路由 |
| CI/CD | GitHub Actions | 与 Issue/PR 流程天然集成 |
| 配置 | 环境变量 + 华为云凭据管理（密钥托管） | 密钥不入库 |
| 日志/监控 | 华为云 AOM / LTS + 基础指标 | 统一纳管日志与监控 |

> 重要：模型密钥、数据库口令等敏感配置 **禁止入库**，统一通过环境变量/华为云凭据管理（KMS/凭据管理服务）注入。

---

## 四、数据模型设计

> 约定：主键 `id` 采用 bigint 自增或 UUID；公共字段 `created_at`、`updated_at`、`created_by`、`updated_by`；软删 `deleted_at`。

### 4.1 核心实体 ER 概览

```
user ──< audit_log
user ──< job ──< resume ──< interview
job ──< jd_version
resume ──< resume_match_result
interview ──< interview_eval
dictionary: position_template / skill_dict / competency_template
ai_call_log（全局审计）
```

### 4.2 主要表结构（简化）

#### user（用户）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint PK | |
| username | varchar | 登录名 |
| password_hash | varchar | 加密哈希 |
| name | varchar | 姓名 |
| role | varchar | HR / HR_LEAD / INTERVIEWER / ADMIN |
| status | varchar | 启用/禁用 |
| created_at / updated_at | timestamp | |

#### job（岗位）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint PK | |
| title | varchar | 岗位名称 |
| level | varchar | 岗位等级 |
| business_req | text | 业务要求 |
| job_profile | jsonb | 岗位画像 |
| skill_requirements | jsonb | 技能要求 |
| status | varchar | 草稿/发布/关闭 |
| created_by / created_at | | |

#### jd_version（JD 版本，支持编辑与版本留痕）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint PK | |
| job_id | bigint FK | |
| version_no | int | 版本号 |
| content | jsonb | JD 完整内容 |
| source | varchar | AI 生成 / 人工编辑 |
| created_by / created_at | | |

#### resume（简历）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint PK | |
| candidate_name | varchar | 脱敏存储可选 |
| file_ref | varchar | 对象存储引用（加密文件） |
| parsed_data | jsonb | 结构化解析结果 |
| status | varchar | 待筛选/面试/录用/淘汰 |
| job_id | bigint FK | 目标岗位 |
| retention_until | date | 留存截止；**永久保留场景置空** |
| created_at | | |

#### resume_match_result（匹配评分结果）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint PK | |
| resume_id | bigint FK | |
| job_id | bigint FK | |
| match_score | int | 0–100 |
| advantages | jsonb | 优势 |
| risks | jsonb | 风险 |
| rationale | jsonb | 评分依据（命中/缺失项） |
| ai_call_log_id | bigint FK | 关联审计 |
| created_at | | |

#### interview（面试）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint PK | |
| resume_id | bigint FK | |
| job_id | bigint FK | |
| record_text | text | 面试记录 |
| status | varchar | 已录入/已评价 |
| created_by / created_at | | |

#### interview_eval（面试评价）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint PK | |
| interview_id | bigint FK | |
| summary | text | 面试总结 |
| capability_eval | jsonb | 能力评价（按维度） |
| recommendation | varchar | 推荐/待定/不推荐 |
| rationale | jsonb | 依据 |
| ai_call_log_id | bigint FK | |
| created_at | | |

#### ai_call_log（AI 调用审计）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint PK | |
| agent_type | varchar | JobAgent / ResumeAgent / InterviewAgent |
| model | varchar | 模型名 |
| prompt_version | varchar | 提示词版本 |
| input_digest | varchar | 输入摘要/哈希 |
| output_digest | varchar | 输出摘要 |
| latency_ms | int | 耗时 |
| status | varchar | 成功/失败 |
| operator_id | bigint FK | 操作人 |
| created_at | | |

#### dictionary 表（P1，岗位库/技能字典/能力模板）
- `position_template`（岗位模板）、`skill_dict`（技能字典）、`competency_template`（能力维度模板）：MVP 可先内置一份默认能力模板用于面试评价标准化，其余 P1 落库管理。

### 4.3 数据合规与安全

- **加密**：简历文件对象存储加密；`parsed_data` 中敏感字段（手机、身份证、住址）入库前脱敏或加密列存储。
- **留存与删除**：简历 **永久保留**（`retention_until` 取消/置空，不触发自动清理）；导出接口满足个人信息可携带要求；删除操作为人工显式触发（合规审计），不设自动过期。
- **审计**：`ai_call_log` 只增不删，满足可审计。
- **权限**：基于 `user.role` 控制数据可见范围（如 HR 仅看本人/本团队简历）。

---

## 五、核心业务流程

### 5.1 JD 生成流程（F1）

```
HR 输入岗位信息(名称/等级/业务要求)
        │
        ▼
应用层 JobService.createJobDraft()
        │
        ▼
AgentOrchestrator.invoke(JobAgent, ctx)
        │  ├─ PromptManager 构建提示词(vN)
        │  ├─ LLMClient 调用(结构化输出)
        │  └─ OutputParser 校验 + 抽取 rationale
        ▼
返回 {jd, job_profile, skill_requirements, rationale}
        │
        ▼
落库 job + jd_version(source=AI)，写 ai_call_log
        │
        ▼
HR 在前端编辑 JD → 保存新版本 jd_version(source=HUMAN)
```

**接口示意**：`POST /api/jobs/draft` → `{ job_id, jd, job_profile, skill_requirements, rationale }`

### 5.2 简历分析流程（F2）

```
HR 上传简历(PDF/Word) + 选择目标岗位
        │
        ▼
ResumeService.upload(): 存对象存储(加密) → resume 记录
        │
        ▼
ResumeParser 解析 → parsed_data(结构化)
        │
        ▼
AgentOrchestrator.invoke(ResumeAgent, {parsed_data, job_profile, skill_requirements})
        │  ├─ 对齐岗位技能项
        │  ├─ LLM 评分 + 优势/风险推理
        │  └─ 输出 match_score + rationale(命中/缺失)
        ▼
落库 resume_match_result，写 ai_call_log
        │
        ▼
返回 {match_score, advantages, risks, rationale}
        │
        ▼
HR 按评分排序查看，更新 resume.status
```

**接口示意**：`POST /api/resumes/upload` → `resume_id`；`POST /api/resumes/{id}/analyze` → 匹配结果。

### 5.3 面试评价流程（F3）

```
面试官录入面试记录(文本) + 关联简历/岗位
        │
        ▼
InterviewService.createRecord()
        │
        ▼
AgentOrchestrator.invoke(InterviewAgent, {record, job_profile, competency_template})
        │  ├─ 按能力维度模板对齐
        │  ├─ LLM 生成 summary / capability_eval / recommendation
        │  └─ 附 rationale
        ▼
落库 interview_eval，写 ai_call_log
        │
        ▼
返回 {summary, capability_eval, recommendation, rationale}
        │
        ▼
面试官确认/修正 → 归档
```

**接口示意**：`POST /api/interviews` → `interview_id`；`POST /api/interviews/{id}/evaluate` → 评价结果。

### 5.4 AI 调用通用时序（横切）

```
前端请求 → API Gateway(鉴权/限流) → 应用服务 → AgentOrchestrator
        │
        ├─ 取操作人上下文 / 校验权限
        ├─ PromptManager 取模板(vN)
        ├─ LLMClient 调用(重试/超时)
        ├─ OutputParser 校验
        ├─ 写 ai_call_log(审计)
        └─ 结果落业务表 → 返回前端
```

### 5.5 招聘数据分析流程（P1，F4）

```
HR 负责人选择时间区间
        │
        ▼
AnalyticsService.query(): 基于 job/resume/interview 聚合
        │
        ▼
返回招聘周期/漏斗转化率/渠道效果 → 前端 ECharts 看板
```

### 5.6 权限与审计流程（F5）

```
登录 → 颁发 JWT(含 role) → 请求携带 JWT
        │
        ▼
网关/服务校验 JWT + 角色权限 → 放行/拒绝
        │
        ▼
关键操作(AI 调用/简历增删/配置变更) → 审计记录
```

---

## 六、关键技术约束与取舍

1. **MVP 不引入消息队列与微服务**：以模块化单体 + 同步调用为主，仅在 P1 批量/异步场景引入 Celery；避免过度设计。
2. **向量匹配延后**：MVP 简历匹配以结构化技能项 + LLM 推理实现；语义向量匹配在 P1 验证必要性后再引入 pgvector。
3. **LLM 依赖隔离**：统一 `LLMClient` 接口，业务模块不直接耦合具体模型；切换/多模型不影响上层。
4. **结构化输出优先**：所有 AI 输出走 JSON Schema 约束，降低解析不确定性，提升可测试性。
5. **合规前置**：简历加密、留存、删除/导出在 MVP 即落地，不留合规债。

---

## 七、技术任务拆解（概览）

> 详细任务清单与依赖将在开发阶段由 Developer Agent 细化，此处给出主线。

| Task | 内容 | 依赖 | 完成标准 |
|---|---|---|---|
| T1 | 工程脚手架（前后端、CI、Docker） | — | 可本地启动、CI 通过 |
| T2 | 用户/角色/权限 + JWT 鉴权 | T1 | 登录与角色可见性验证通过 |
| T3 | AI Agent 基座（Orchestrator/PromptManager/LLMClient/OutputParser）+ 审计；LLMClient 接入华为云盘古 | T1 | 三 Agent 可调用并写日志 |
| T4 | AI 职位助手（JD 生成）端到端 | T2,T3 | JD 生成 ≤15s、含依据 |
| T5 | AI 简历分析助手（上传/解析/评分） | T2,T3 | 简历评分 ≤20s、含依据、加密存储 |
| T6 | AI 面试助手（评价/推荐） | T2,T3 | 输出总结/评价/推荐、含依据 |
| T7 | 简历合规（永久保留 + 删除/导出审计） | T5 | 删除/导出可用、删除有审计、无自动清理 |
| T8 | 招聘数据分析看板（P1） | T4,T5,T6 | 看板 ≥3 指标、查询 ≤5s |
| T9 | 批量/异步与字典管理（P1） | T5,T3 | 批量筛选排序、岗位库可用 |

---

> **完成标准自检**：✅ 与 PRD 一致 ｜ ✅ 架构清晰 ｜ ✅ 接口明确 ｜ ✅ 数据模型明确 ｜ ✅ 开发任务可执行

> **人工确认结论（2026-07-18，已确认）**：
> 1. 技术栈：**Python + FastAPI**（已采纳，备选 Java 方案不采用）；
> 2. LLM 提供方与密钥管理：**华为云盘古大模型**，AK/SK 经华为云凭据管理（DEW/KMS）托管注入，统一 LLMClient 适配层接入（详见 3.4.1）；
> 3. 部署环境与对象存储：**华为云**（RDS for PostgreSQL、OBS、DCS for Redis、AOM/LTS）；
> 4. 数据留存与删除策略：简历 **永久保留**，不设自动过期/清理；删除为人工显式触发并留审计；导出接口支持个人信息可携带。

> **新增待确认项**（实施阶段需跟进）：
> a) 华为云盘古具体模型版本与 API 端点（依可用模型清单最终选定，接入点在 `HuaweiClient`）；
> b) 华为云区域与网络互通（VPC、子网、安全组、OBS/RDS/盘古同区规划）；
> c) 永久保留下的存储与备份成本评估（OBS 生命周期 + RDS 备份策略）；
> d) 简历永久保留的合规告知（用户隐私声明/授权范围需法务确认）。
