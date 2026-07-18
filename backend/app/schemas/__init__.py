"""Pydantic schema 集合。"""
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.job import JobDraftRequest, JobDraftResult, JobUpdateRequest

__all__ = [
    "LoginRequest",
    "RefreshRequest",
    "TokenResponse",
    "JobDraftRequest",
    "JobDraftResult",
    "JobUpdateRequest",
]
