"""API 路由聚合。"""
from fastapi import APIRouter

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.dictionary import router as dictionary_router
from app.api.health import router as health_router
from app.api.interview import router as interview_router
from app.api.job import router as job_router
from app.api.resume import router as resume_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(job_router)
api_router.include_router(resume_router)
api_router.include_router(interview_router)
api_router.include_router(analytics_router)
api_router.include_router(dictionary_router)
