"""日志：结构化日志，便于华为云 LTS 纳管。"""
import logging
import sys

import structlog

from app.config import settings

_CONFIGURED = False


def setup_logging() -> None:
    """配置 structlog（幂等，避免重复配置报错）。"""
    global _CONFIGURED
    if _CONFIGURED:
        return
    level = logging.DEBUG if settings.app_debug else logging.INFO
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.app_debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.WriteLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    if not _CONFIGURED:
        setup_logging()
    return structlog.get_logger(name)
