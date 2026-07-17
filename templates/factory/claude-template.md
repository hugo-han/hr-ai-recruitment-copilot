# Claude Runtime Context

> OPC AI Software Factory 自动生成文件

---

# 项目信息

项目名称：

{{PROJECT_NAME}}


项目描述：

{{PROJECT_DESCRIPTION}}


---

# AI Context Registry

## 企业上下文

路径：

.factory/context/enterprise.md


用途：

定义企业级开发规范、技术约束和治理规则。


---

## 项目上下文

路径：

.factory/context/project.md


用途：

定义当前项目目标、范围和业务背景。


---

## 工作流上下文

路径：

.factory/context/workflow.md


用途：

定义AI Agent协作流程。


---

# Agent Registry


## Product Agent

路径：

.factory/agents/product-agent.md


职责：

需求分析、PRD生成、业务拆解。


---

## Architect Agent

路径：

.factory/agents/architect-agent.md


职责：

系统设计、架构决策、技术方案。


---

## Developer Agent

路径：

.factory/agents/developer-agent.md


职责：

代码实现、重构和优化。


---

## QA Agent

路径：

.factory/agents/qa-agent.md


职责：

测试设计、质量验证。


---

## Release Agent

路径：

.factory/agents/release-agent.md


职责：

发布管理、版本控制。


---

# AI Execution Rules


1. 所有开发活动必须遵循项目上下文。

2. Agent执行前必须读取对应角色定义。

3. 大型任务必须拆分为多个Agent协作流程。

4. CLAUDE.md只作为入口索引，不存储详细知识。


---

# Context Loading Strategy


默认加载：

- enterprise.md
- project.md
- workflow.md


按需加载：

- agents/*.md
- docs/*.md

