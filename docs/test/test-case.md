# HR 招聘 AI 助手 测试用例（Test Cases）

| 项 | 内容 |
|---|---|
| 项目名称 | hr-ai-recruitment-copilot |
| 文档版本 | v1.5 |
| 编写角色 | QA Agent |
| 编写日期 | 2026-07-18 |
| 输入依据 | docs/test/test-plan.md、docs/product/PRD.md、docs/architecture/system-design.md、docs/development/mvp-development-plan.md |
| 文档状态 | Draft（测试先行，随开发交付逐步执行） |

> 修订记录：v1.0 首批用例；v1.1 巡检 #1 补充用例登记（§13.1）；v1.2 巡检 #2 对齐 mvp-development-plan.md（T1–T7 完成、48 passed），新增 Alembic 迁移验证用例与 R-10/R-11 相关用例登记；v1.3 巡检 #3 R-10 解除（obs-local 已出库并补 .gitignore），登记 R-13（docs/test staged 版本滞后），本轮无新代码变更。

> 用例格式：`编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型`
> 优先级：P0 阻塞级 / P1 严重 / P2 一般；类型：功能(F) / 接口(API) / AI质量(AI) / 性能(P) / 安全合规(S) / 集成(I)
> 用例编号规则：模块段位——001 基础设施 / 1xx 鉴权 / 2xx AI 基座 / 3xx 职位 / 4xx 简历 / 5xx 面试 / 6xx 分析 / 7xx 合规 / 8xx E2E / 9xx 非功能。

---

## 一、健康检查与基础设施（T1）

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-001 | health | 探活正常 | 服务启动 | `GET /api/health` | 200，`code=0`，`data.status=healthy` | P0 | API |
| TC-002 | health | 无 DB 依赖 | 仅启动服务 | `GET /api/health` 多次 | 稳定 200，不依赖 DB | P1 | API |
| TC-003 | CI | 后端 lint 通过 | 安装依赖 | `ruff check app tests` | 退出码 0 | P1 | F |
| TC-004 | CI | 后端单测通过 | 安装依赖 | `pytest -q` | 全部通过 | P0 | F |
| TC-005 | CI | 前端构建通过 | `npm ci` | `npm run build` | 产物 dist 生成 | P0 | F |

---

## 二、用户/角色/权限与鉴权（T2 / F5.1）

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-101 | auth | 正确登录 | 存在用户 | `POST /api/auth/login` 正确账号密码 | 200，`code=0`，返回 access/refresh token | P0 | API |
| TC-102 | auth | 密码错误 | 存在用户 | 错误密码 | 401/400，`code!=0`，不返回 token | P0 | API |
| TC-103 | auth | 无 token 访问受保护接口 | 未登录 | `GET /api/jobs` 无 Authorization | 401 | P0 | S |
| TC-104 | auth | token 过期 | token 已过期 | 携带过期 token | 401，可刷新 | P1 | S |
| TC-105 | auth | refresh 续签 | 持有有效 refresh | `POST /api/auth/refresh` | 200，返回新 access | P0 | API |
| TC-106 | auth | 越权访问 | HR 角色登录 | 访问仅 ADMIN 接口 | 403 | P0 | S |
| TC-107 | auth | 面试官访问简历 | INTERVIEWER 登录 | 访问非授权简历 | 403 或范围受限 | P0 | S |
| TC-108 | auth | 密码哈希存储 | 注册/初始化后 | 查 `user.password_hash` | 非明文，bcrypt 等哈希 | P0 | S |

---

## 三、AI Agent 基座（T3 / F5.4）

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-201 | LLMClient | Mock 调用返回结构化 | provider=mock | 构造 messages+schema | 返回 `content/parsed/usage/latency`，parsed 合规 | P0 | F |
| TC-202 | LLMClient | HuaweiClient 切换不侵入业务 | provider=huawei | 业务层统一调用 | 业务代码不变，实现类切换 | P0 | I |
| TC-203 | LLMClient | 失败重试 | mock 抛错 2 次 | 第 3 次成功 | 重试 2 次后成功，记录 latency | P1 | F |
| TC-204 | LLMClient | 超时 | mock 30s 不返回 | 调用 | 30s 超时，返回明确错误 | P1 | P |
| TC-205 | PromptManager | 版本化取模板 | 存在 v1 | 取模板 v1 | 返回 v1 内容与版本号 | P0 | F |
| TC-206 | OutputParser | 合法 JSON 解析 | LLM 返回合法 JSON | 解析 | 解析成功，字段齐全 | P0 | F |
| TC-207 | OutputParser | 非法 JSON 重试/降级 | LLM 返回非法 JSON | 解析 | 触发重试或降级，不抛裸文本 | P0 | F |
| TC-208 | audit | 写 ai_call_log | 任意 Agent 调用 | 调用后查库 | 生成记录，字段齐全 | P0 | S |
| TC-209 | audit | 审计只增不删 | 已有记录 | 尝试删除/更新 | 接口不允许，记录保留 | P0 | S |
| TC-210 | Orchestrator | 鉴权上下文透传 | 未登录调用 Agent | 调用 | 拒绝或记录 operator 为空非法 | P0 | S |

---

## 四、AI 职位助手（F1 / T4）

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-301 | job | 正常生成 JD | 登录 | `POST /api/jobs/draft` 含名称/等级/业务要求 | 200，返回 jd/job_profile/skill_requirements/rationale | P0 | API |
| TC-302 | job | 字段完整 | 同上 | 输出 | 三部分字段完整率 ≥95% | P0 | AI |
| TC-303 | job | 含依据 | 同上 | 输出 rationale | 非空，可解释 | P0 | AI |
| TC-304 | job | 性能 ≤15s | 同上 | 计时 | ≤15s | P0 | P |
| TC-305 | job | 缺字段校验 | 登录 | 缺岗位名称 | 422 | P0 | API |
| TC-306 | job | 版本留痕 | 已生成 | 编辑后保存 | 生成新 jd_version，source=HUMAN | P0 | F |
| TC-307 | job | 超长业务要求 | 登录 | 极长文本 | 不报错，正常返回或分段处理 | P1 | F |
| TC-308 | job | AI 调用写审计 | 生成后 | 查 ai_call_log | 含 agent_type=JobAgent | P0 | S |
| TC-309 | job | 越权 | 面试官登录 | 调用 draft | 403 或受限 | P1 | S |

---

## 五、AI 简历分析助手（F2 / T5）

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-401 | resume | 上传 PDF | 登录，存在岗位 | 上传文本型 PDF + job_id | 200，返回 resume_id | P0 | API |
| TC-402 | resume | 上传 Word | 同上 | 上传 .docx | 200，可解析 | P0 | API |
| TC-403 | resume | 非法格式 | 同上 | 上传 .exe | 400，拒绝 | P0 | API |
| TC-404 | resume | 文件加密存储 | 上传后 | 查 OBS | 文件已加密，非明文 | P0 | S |
| TC-405 | resume | 解析结构化 | 上传后 | 解析结果 | parsed_data 结构化，关键字段存在 | P0 | AI |
| TC-406 | resume | 匹配评分 0-100 | 上传+岗位 | `POST /api/resumes/{id}/analyze` | 返回 0–100 整数评分 | P0 | API |
| TC-407 | resume | 优势/风险输出 | 同上 | 输出 | advantages/risks 非空 | P0 | AI |
| TC-408 | resume | 评分依据 | 同上 | rationale | 含命中/缺失项 | P0 | AI |
| TC-409 | resume | 性能 ≤20s | 同上 | 计时 | ≤20s | P0 | P |
| TC-410 | resume | 脱敏进 LLM | 调用前 | 送入文本 | 无明文身份证/手机/住址 | P0 | S |
| TC-411 | resume | 排序展示（P1） | 多份简历 | `GET /api/resumes?sort=score` | 按评分降序 | P1 | API |
| TC-412 | resume | 缺岗位 | 未选岗位 | analyze | 400/422 | P0 | API |
| TC-413 | resume | 解析失败降级 | 损坏文件 | 上传 | 返回明确错误，不崩溃 | P1 | F |

---

## 六、AI 面试助手（F3 / T6）

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-501 | interview | 录入面试记录 | 登录，存在简历/岗位 | `POST /api/interviews` 含 record_text | 200，返回 interview_id | P0 | API |
| TC-502 | interview | 生成评价 | 录入后 | `POST /api/interviews/{id}/evaluate` | 返回 summary/capability_eval/recommendation/rationale | P0 | API |
| TC-503 | interview | 推荐三选一 | 同上 | recommendation | ∈ {推荐,待定,不推荐} | P0 | AI |
| TC-504 | interview | 能力维度覆盖 | 同上 | capability_eval | 覆盖能力模板全部维度 | P0 | AI |
| TC-505 | interview | 含依据 | 同上 | rationale | 非空，可解释 | P0 | AI |
| TC-506 | interview | 空记录 | 登录 | 空 record_text | 422 | P1 | API |
| TC-507 | interview | 超长转写 | 登录 | 极长文本 | 分段处理，正常返回 | P1 | F |
| TC-508 | interview | 越权 | HR 角色改他人面试 | 调用 | 403 或范围受限 | P1 | S |
| TC-509 | interview | 审计 | 评价后 | ai_call_log | agent_type=InterviewAgent | P0 | S |

---

## 七、招聘数据分析（F4，P1 / T8）

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-601 | analytics | 看板指标 | 存在数据 | `GET /api/analytics/overview` | 返回 ≥3 指标（周期/转化率/渠道） | P1 | API |
| TC-602 | analytics | 时间筛选 | 同上 | 带 start/end 参数 | 仅返回区间数据 | P1 | API |
| TC-603 | analytics | 性能 ≤5s | 同上 | 计时 | ≤5s | P1 | P |
| TC-604 | analytics | 无数据兜底 | 无数据 | 查询 | 返回空结构，不报错 | P1 | F |
| TC-605 | analytics | 越权 | 非负责人 | 查询 | 403 或范围受限 | P1 | S |

---

## 八、简历合规（T7 / F5.5）

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-701 | resume | 永久保留 | 上传简历 | 不触发清理 | 文件与记录永久存在，无自动过期 | P0 | S |
| TC-702 | resume | 人工删除留审计 | 登录 ADMIN | `DELETE /api/resumes/{id}` | 删除成功，写审计，retention 不触发 | P0 | S |
| TC-703 | resume | 删除越权 | 非授权角色 | 调用删除 | 403 | P0 | S |
| TC-704 | resume | 导出 | 登录 | `GET /api/resumes/{id}/export` | 返回可下载文件，含个人信息 | P0 | API |
| TC-705 | resume | 导出审计 | 导出后 | 查审计 | 记录导出操作 | P0 | S |
| TC-706 | resume | 敏感字段加密 | 上传后 | 查 parsed_data | 身份证/手机等加密或脱敏存储 | P0 | S |

---

## 九、端到端集成（闭环）

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-801 | e2e | 招聘全闭环 | 登录+MockClient | 生成 JD → 上传简历评分 → 录入面试评价 | 全链路成功，各步有依据与审计 | P0 | I |
| TC-802 | e2e | 多角色协作 | 多角色账号 | HR 上传→面试官评价→负责人看板 | 权限隔离正确，数据贯通 | P0 | I |
| TC-803 | e2e | AI 失败不影响闭环 | MockClient 强制失败 | 跑闭环 | 失败步骤明确报错，其余可重试 | P1 | I |

---

## 十、非功能与安全

| 编号 | 模块 | 场景 | 前置条件 | 输入 | 期望结果 | 优先级 | 类型 |
|---|---|---|---|---|---|---|---|
| TC-901 | perf | JD 并发 | 登录 | 并发 10 次 draft | 全部 ≤15s，无 5xx | P1 | P |
| TC-902 | perf | 简历并发 | 登录 | 并发 10 次 analyze | 全部 ≤20s | P1 | P |
| TC-903 | security | SQL 注入 | 登录 | 入参含 `' OR 1=1--` | 正常转义/拒绝，无数据泄露 | P0 | S |
| TC-904 | security | XSS | 前端 | JD/记录含 `<script>` | 转义渲染，不执行 | P1 | S |
| TC-905 | security | 敏感配置不入库 | 检查仓库 | grep AK/SK/口令 | 无明文密钥提交 | P0 | S |
| TC-906 | security | 日志无明文简历 | 调用后 | 查日志/审计 | 仅摘要/哈希，无明文 | P0 | S |
| TC-907 | availability | 服务重启可用 | 重启后 | health | 恢复 200 | P1 | F |

---

## 十一、用例统计

| 优先级 | 代表用例 |
|---|---|
| P0 | TC-001/004/005、101/102/103/105/106/107/108、201/205/206/207/208/209/210、301~305/308、401~410/412、501~505/509、701~706、801/802、903/905/906 等 |
| P1 | TC-002/003、104、203/204、307/309、411/413、506/507/508、601~605、803、901/902/904/907 等 |
| P2 | 暂无（远期增强随 P2 迭代补充） |

| 类型 | 覆盖 |
|---|---|
| F 功能 | TC-003/004/005/206/207/306/307/413/507/604/907 等 |
| API 接口 | 001/101/105/301/401/502/601/704 等 |
| AI 质量 | 302/303/405/407/408/503/504/505 等 |
| P 性能 | 204/304/409/603/901/902 |
| S 安全合规 | 103/104/106/107/108/208/209/210/308/410/701–706/903–906 |
| I 集成 | 202/801/802/803 |

---

## 十二、验收标准 ↔ 用例追踪

| 验收标准 | 关联用例 |
|---|---|
| AC-US-01 JD 生成 | TC-301、TC-302、TC-303、TC-304、TC-306 |
| AC-US-02 简历分析 | TC-401、TC-402、TC-405、TC-406、TC-407、TC-408、TC-411 |
| AC-US-03 面试助手 | TC-502、TC-503、TC-504、TC-505 |
| AC-US-04 数据分析（P1） | TC-601、TC-602、TC-603 |
| AC-US-06 权限与审计 | TC-103、TC-106、TC-107、TC-208、TC-209、TC-404、TC-410、TC-706、TC-906 |
| AC-US-08 合规删除/导出 | TC-701、TC-702、TC-703、TC-704、TC-705 |

---

## 十三、用例执行追踪（随开发交付更新）

| 里程碑 | 关联用例 | 状态（v1.1 巡检 #1，2026-07-18） |
|---|---|---|
| M2 脚手架 | TC-001~005 | ✅ test_health.py 2 passed；CI 未跑 |
| M3 T2 鉴权 | TC-101~108 | ✅ test_auth.py 8 + test_authz.py 2 passed |
| M3 T3 基座 | TC-201~210 | ✅ test_ai_agent.py 9 passed（含审计无明文 TC-208/906） |
| M3 T4 职位 | TC-301~309 | ✅ test_job.py 7 passed（含落库/审计/版本留痕/401/422/404） |
| M3 T5 简历 | TC-401~413 | ✅ test_resume.py 12 passed（含上传/评分区间/脱敏/排序/软删/导出/审计） |
| M3 T6 面试 | TC-501~509 | ✅ test_interview.py 8 passed（含推荐枚举/维度覆盖/依据/审计/401） |
| M3 T7 合规 | TC-701~706 | ✅ 含于 test_resume.py（软删不物理删 + 重复删除 409 + 导出） |
| M4 集成 | TC-801~803 | ⏳ 待补 E2E 串联用例（三助手闭环） |
| M5 AI 评测 | TC-302/303/405/407/408/503/504 | ⏳ 待黄金评测集就绪（Mock 已可断言结构/依据，真实模型待盘古） |
| M6 验收 | AC-US-01~08 | ⏳ 发布前 |
| T8 数据分析（P1） | TC-601~605 | ✅ 巡检 #14：test_analytics.py 6 passed（空数据/漏斗/时间筛选/RBAC 403/HR_LEAD 200/性能 ≤5s）；commit 206c196 |
| T9 批量/字典（P1） | TC-411 等 | ✅ 巡检 #15：test_t9.py 12 passed（字典 CRUD + 技能唯一约束 + 默认模板独占 + 读写 RBAC + 批量异步 eager + API）；commit bfe5ecb |

> 全量后端自动化：**48 passed**（pytest -q，20+ 次复跑稳定）。
> 禁止删除失败用例或隐瞒问题；发现的缺陷以 GitHub Issue（Bug）登记。
> 本轮未稳定复现的 5 failed（首轮）已登记为 test-plan R-09，持续观测。

### 13.1 QA 补充用例登记（待落代码）

| 编号 | 模块 | 场景 | 优先级 | 类型 | 状态（v1.2） |
|---|---|---|---|---|---|
| TC-219 | audit | GET /api/audit/ai-calls 接口未实现 | P0 | API | 待开发交付后补测 |
| TC-308b | job | JD 生成接口层（/api/jobs/draft）成功路径 e2e | P0 | API | 待补（现有 test_job 多走 service 层） |
| TC-410b | resume | /api/resumes/upload 接口层 e2e（multipart） | P0 | API | 待补 |
| TC-502b | interview | /api/interviews/{id}/evaluate 接口层 e2e | P0 | API | 待补（现有仅 401 校验） |
| TC-801 | e2e | 三助手闭环串联（job→resume→interview） | P0 | I | 待补 |
| TC-908 | security | 简历删除/导出 RBAC（应限 HR_LEAD/ADMIN） | P0 | S | ✅ R-11 已修复（commit bfe5ecb，resume.py:52/58 已加 require_roles）；GitHub Issue #1 已关闭；自动化回归用例待补 |
| TC-909 | migration | Alembic init_schema 在 SQLite 升级成功、表齐全 | P0 | F | ✅ 已手工验证（巡检 #2：8 表生成）；建议落 pytest 用例固化 |
| TC-910 | repo-hygiene | `.obs-local/` 不应入库（应被 .gitignore） | P0 | S | ✅ 已解除（巡检 #3：移出暂存区并补入 `backend/.gitignore`，暂存区 0 文件）；残留：.gitignore 改动 unstaged |
| TC-911 | config | 生产配置密钥不入库（AK/SK/口令） | P0 | S | ✅ 巡检 #2 检查：暂存区无 .env/.key/.pem；持续监控 |

> 注：QA 发现 `DELETE /api/resumes/{id}` 与 `GET /api/resumes/{id}/export` 当前仅校验登录（`get_current_user`），未做 `require_roles`/`require_scope` 角色门禁——与 test-plan §7.1 约定的 "HR_LEAD/ADMIN" 不符。此为潜在 P0 安全合规缺口（R-11），登记为 TC-908，待开发补门禁后补测；不在本轮擅自改业务代码。
>
> 巡检 #2 新增：TC-909（Alembic 迁移已手工验证，建议落自动化用例）；TC-910（`.obs-local` 仓库卫生，开发者需处理）；TC-911（密钥不入库检查通过）。

### 13.2 mvp-development-plan 对齐说明

| mvp-plan 声称 | QA 实测（巡检 #2） | 结论 |
|---|---|---| 
| T1–T7 全部完成 | 48 passed，ruff clean | ✅ 一致 |
| T2 "7 用例通过" | test_auth.py 8 + test_authz.py 2 = 10 | 🟡 数量略多于声明（非问题，覆盖更广） |
| T3 "8 用例通过" | test_ai_agent.py 9 | 🟡 略多 |
| T5 "13 用例通过" | test_resume.py 12 | 🟡 略少 1（声明含 T7，实际 T7 用例并入 T5） |
| T6 "8 用例通过" | test_interview.py 8 | ✅ 一致 |
| "HuaweiClient 鉴权占位" | 代码确认 `_build_auth_token` 为占位 | ✅ 与 R-02 一致 |
| "48 passed" | 48 passed | ✅ 一致 |

---

> **完成标准自检**：✅ 用例覆盖 PRD 各功能 ｜ ✅ 覆盖 AI 质量标准 ｜ ✅ 覆盖接口契约 ｜ ✅ 覆盖验收标准 ｜ ✅ 覆盖安全合规 ｜ ✅ 可追踪
