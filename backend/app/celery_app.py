"""Celery 应用配置。

生产：broker=redis://（华为云 DCS），使用环境变量注入。
测试：task_always_eager=True（任务同步执行，无需启动 broker）。
"""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "hr_copilot",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    # 测试环境由 conftest 通过 CELERY_TASK_ALWAYS_EAGER=true 覆盖
)

celery_app.autodiscover_tasks(["app.tasks"])
