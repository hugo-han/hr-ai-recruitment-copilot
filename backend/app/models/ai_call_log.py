"""ai_call_log 表：AI 调用审计，只增不删。对应 PRD F5.4 / system-design 4.2。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# SQLite 不支持 BigInteger 自增主键，用 with_variant 保持生产 PG 用 BigInteger、测试 SQLite 用 Integer
_bigint_autoinc = BigInteger().with_variant(Integer(), "sqlite")


class AiCallLog(Base):
    __tablename__ = "ai_call_log"

    id: Mapped[int] = mapped_column(_bigint_autoinc, primary_key=True, autoincrement=True)
    agent_type: Mapped[str] = mapped_column(String(32), index=True)   # JobAgent / ResumeAgent / InterviewAgent
    model: Mapped[str] = mapped_column(String(64), default="")
    prompt_version: Mapped[str] = mapped_column(String(32))
    input_digest: Mapped[str] = mapped_column(String(128))   # 输入摘要/哈希，不存明文
    output_digest: Mapped[str] = mapped_column(String(128), default="")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16))          # success / failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

