# GitHub Label Strategy

## OPC AI Software Factory Label规范


---

# 一、类型标签 Type


## feature


用途：

新功能需求


示例：
type:feature


---


## bug


用途：

缺陷问题

type:bug


---


## task


用途：

技术任务

type:task


---


## documentation


用途：

文档更新

type:docs


---

# 二、Agent标签


## Product Agent

agent:product


表示：

需要产品分析。



---


## Architect Agent

agent:architect


表示：

需要技术设计。



---


## Developer Agent

agent:developer


表示：

进入开发。



---


## QA Agent

agent:qa


表示：

进入测试。



---


## Release Agent

agent:release


表示：

进入发布。



---

# 三、状态标签 Status


## backlog


待处理

status:backlog


---


## analysis


分析中

status:analysis


---


## development


开发中

status:development


---


## testing


测试中

status:testing


---


## released


已发布

status:released


---

# 四、优先级 Priority

priority:P0
priority:P1
priority:P2
priority:P3


---

# 五、AI生成标识


AI Agent产生的任务：

ai-generated


人工确认：

human-reviewed


---

# 六、推荐默认流程


Feature:
type:feature
↓
agent:product
↓
status:analysis
↓
agent:architect
↓
agent:developer
↓
agent:qa
↓
agent:release
↓
status:released