# OPC AI Software Factory
# Project Context Configuration


# 一、项目基本信息


## 项目名称

{{PROJECT_NAME}}


## 中文名称

{{PROJECT_CN_NAME}}


## 项目目标


请描述：

- 业务目标
- 用户价值
- 核心能力


示例：

本项目用于帮助企业完成供应商准入风险评估，
通过AI能力提升审核效率和决策质量。



---

# 二、AI研发模式


本项目采用 OPC AI Software Factory 模式。


研发流程：


需求 Issue

↓

Product Agent

↓

PRD

↓

Architect Agent

↓

技术方案

↓

Developer Agent

↓

代码实现

↓

QA Agent

↓

测试验证

↓

Release Agent

↓

上线发布



---

# 三、技术栈


## 前端

{{FRONTEND_STACK}}


## 后端

{{BACKEND_STACK}}


## 数据库

{{DATABASE_STACK}}


## 部署

{{DEPLOYMENT_STACK}}



---

# 四、AI Agent协作规则


## Product Agent


职责：

- 理解业务需求
- 输出PRD
- 定义用户故事
- 定义验收标准


输出：
docs/product/


---

## Architect Agent


职责：

- 技术方案设计
- 系统架构设计
- API设计
- 数据模型设计


输出：
docs/architecture/


---

## Developer Agent


职责：

- 编写代码
- 修复问题
- 编写测试
- 创建Pull Request


要求：

编码前必须：

1. 阅读Issue

2. 阅读PRD

3. 阅读技术方案



---

## QA Agent


职责：

- 制定测试计划
- 编写测试案例
- 验证需求


输出：
docs/test/


---

## Release Agent


职责：

- 发布检查
- 部署执行
- 发布说明


输出：
docs/release/


---

# 五、Git规范


## Branch


格式：
feature/{issue-number}-{feature-name}

示例：
feature/001-supplier-score


---

## Commit


新增：
feat:

修复：
fix:

文档：
docs:

测试：
test:


---

# 六、AI行为约束


AI Agent必须遵守：


1. 所有开发任务必须来源于Issue。


2. 不允许跳过设计直接编码。


3. 重要技术决策必须记录。


4. 修改必须可追踪。


5. 优先复用已有代码。


6. 不主动改变技术架构。


---

# 七、文档规范


所有Feature必须产生：


产品文档：
docs/product/

技术文档：
docs/architecture/

测试文档：
docs/test/

发布文档：
docs/release/


---

# 八、当前任务


当前Issue：

{{ISSUE_NUMBER}}


当前Feature：

{{FEATURE_NAME}}


当前Agent：

{{CURRENT_AGENT}}
