# OPC AI Software Factory
# Claude Context Assembly Design v1.0


## 1. 目标


定义项目初始化过程中 AI 上下文生成机制。


目标：

让 Claude Code、Codex、未来 MCP Agent 在进入项目后，可以自动理解：

- 企业规则
- 项目背景
- 技术约束
- Agent职责
- 开发流程



---

# 2. Context来源


最终生成：
CLAUDE.md

来源：

templates/claude
    +
agents
    +
project metadata
    +
repository information


---

# 3. Context结构


生成后的 CLAUDE.md：

Project Context
Enterprise Rules
企业级AI开发规范
来源：
CLAUDE.enterprise.md
Project Context
项目级信息
来源：
CLAUDE.project.md
Agent Collaboration
Agent协作规则
来源：
agents/*.md
Development Workflow
研发流程：
Issue
↓
Design
↓
Coding
↓
Testing
↓
Release


---

# 4. Assembly流程

init-project.ps1
    |

    ↓
build-claude-context.ps1
    |

    ↓
读取模板
    |

    ↓
合并上下文
    |

    ↓
生成CLAUDE.md


---

# 5. 输入


参数：


|参数|说明|
|-|-|
|ProjectName|项目名称|
|Description|项目描述|
|FactoryPath|Factory路径|
|ProjectPath|项目路径|



---

# 6. 输出


生成：

Project
└── CLAUDE.md


---

# 7. 设计原则


## Single Context


AI只需要读取一个入口文件。


## Traceable


所有规则来源可追踪。


## Maintainable


模板升级可以重新生成。


## Human Control


重要规则人工确认。


---

# 8. 后续扩展


未来支持：


## MCP Context Server


统一管理：

- 项目知识
- 文档
- Issue
- Code



## Multi Agent Context


不同Agent加载不同上下文：

Product Agent

Architect Agent

Developer Agent

QA Agent

Release Agent

