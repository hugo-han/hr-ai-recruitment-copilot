# hr-ai-recruitment-copilot

HR 招聘 AI 助手 — 由 OPC AI Software Factory 创建。

## 项目结构

```
.
├── docs/                 # 产品 / 架构 / 测试 / 发布文档
├── .factory/             # OPC AI Factory 运行时（Context / Agents）
├── backend/              # FastAPI 后端（Python）
│   ├── app/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
└── frontend/             # React + Vite + TypeScript 前端
    ├── src/
    ├── package.json
    └── Dockerfile
```

## 快速开始

### 后端
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]"
cp .env.example .env            # 填入本地配置
alembic upgrade head            # 数据库迁移（按需）
uvicorn app.main:app --reload   # http://localhost:8000
```

### 前端
```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

## 技术栈
- 后端：Python 3.11 + FastAPI + SQLAlchemy 2.x + Alembic + JWT
- 数据：PostgreSQL / Redis（生产华为云 RDS / DCS）
- AI：华为云盘古大模型，统一 LLMClient 适配层接入
- 前端：React + TypeScript + Vite + Ant Design
- 部署：Docker + 华为云

详见 `docs/architecture/system-design.md`。
