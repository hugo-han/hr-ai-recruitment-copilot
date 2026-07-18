"""Health 路由：用于探活与可观测。"""
from fastapi import APIRouter

from app.common.response import ok

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return ok({"status": "healthy", "service": "hr-ai-recruitment-copilot-backend"})
