"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.common.logging import setup_logging
from app.common.response import register_exception_handlers
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    setup_logging()
    yield
    # 关闭（预留：连接池清理等）


app = FastAPI(
    title="HR 招聘 AI 助手 API",
    version="0.1.0",
    description="hr-ai-recruitment-copilot 后端服务",
    docs_url="/docs" if settings.app_debug else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api")
