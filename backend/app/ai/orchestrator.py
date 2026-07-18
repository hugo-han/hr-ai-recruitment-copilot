"""AgentOrchestrator：统一调度 AI Agent，处理鉴权上下文、审计、限流、结果落库。

对应 system-design 2.2。
"""
import time
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient, digest_text, get_llm_client
from app.ai.output_parser import parse_json_object, require_rationale
from app.ai.prompt_manager import PromptTemplate, get_prompt
from app.common.logging import get_logger
from app.models.ai_call_log import AiCallLog

logger = get_logger(__name__)


class AgentContext:
    """一次 Agent 调用的上下文。"""

    def __init__(self, agent_type: str, operator_id: int | None, prompt_name: str):
        self.agent_type = agent_type
        self.operator_id = operator_id
        self.prompt_name = prompt_name

    @property
    def prompt(self) -> PromptTemplate:
        return get_prompt(self.prompt_name)


class AgentOrchestrator:
    """Agent 调度器：编排提示词构建、LLM 调用、解析、审计。"""

    def __init__(self, db: Session, client: LLMClient | None = None):
        self.db = db
        self.client = client or get_llm_client()

    def invoke(self, ctx: AgentContext, user_message: str, schema: dict | None = None) -> dict[str, Any]:
        """同步调用 Agent，返回解析后的 dict（含 rationale）并写审计。"""
        prompt = ctx.prompt
        messages = [
            {"role": "system", "content": prompt.system},
            {"role": "user", "content": user_message},
        ]
        start = time.time()
        status = "success"
        error: str | None = None
        result: dict[str, Any] = {}
        try:
            raw = self.client.chat(messages, schema=schema)
            result = parse_json_object(raw.content)
            require_rationale(result)
            return result
        except Exception as exc:  # noqa: BLE001
            status = "failed"
            error = str(exc)
            logger.warning("agent_invoke_failed", agent=ctx.agent_type, error=error)
            raise
        finally:
            self._write_log(ctx, prompt, user_message, result, status, error, int((time.time() - start) * 1000))

    def _write_log(
        self,
        ctx: AgentContext,
        prompt: PromptTemplate,
        user_message: str,
        result: dict[str, Any],
        status: str,
        error: str | None,
        latency_ms: int,
    ) -> None:
        log = AiCallLog(
            agent_type=ctx.agent_type,
            model=getattr(self.client, "model", "") if hasattr(self.client, "model") else "",
            prompt_version=prompt.version,
            input_digest=digest_text(user_message),
            output_digest=digest_text(str(result)) if result else "",
            latency_ms=latency_ms,
            status=status,
            error=error,
            operator_id=ctx.operator_id,
        )
        self.db.add(log)
        self.db.commit()
