# Claude Runtime Context

> OPC AI Software Factory Runtime入口

## Project Identity

名称:
{{PROJECT_NAME}}

描述:
{{PROJECT_DESCRIPTION}}

## Context Registry

企业规则:
.factory/context/enterprise.md

项目规则:
.factory/context/project.md

流程规则:
.factory/context/workflow.md

## Agent Registry

产品:
.factory/agents/product-agent.md

架构:
.factory/agents/architect-agent.md

开发:
.factory/agents/developer-agent.md

测试:
.factory/agents/qa-agent.md

发布:
.factory/agents/release-agent.md

## Execution Rules

1. 执行任务前读取项目Context。
2. 根据任务类型选择对应Agent。
3. Agent详细规则按需加载。
4. CLAUDE.md只保存入口信息。
5. 大型任务拆分为多Agent协作。

## Loading Strategy

默认加载:
- enterprise.md
- project.md
- workflow.md

按需加载:
- agents/*.md
- docs/*.md