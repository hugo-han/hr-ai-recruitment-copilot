# Factory Template Version Management Design


## 目标

管理 OPC AI Software Factory 模板生命周期。


## 版本范围

Factory版本包含:

- Agent模板
- Context模板
- Claude Runtime模板
- GitHub模板


## 项目生成

项目创建时:

Factory版本同步到:

.factory/version.yaml


## 升级策略

未来支持:

factory upgrade


流程:

检查当前版本

↓

比较模板差异

↓

生成升级建议

↓

人工确认

