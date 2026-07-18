"""LLMClient 抽象接口与实现。

- LLMClient：统一调用接口，业务模块不耦合具体模型；
- HuaweiClient：华为云盘古接入（生产）；
- MockClient：测试/CI 用，可复现、零外网依赖。

对应 system-design 3.4.1。
"""
import hashlib
import json
import time
from typing import Any, Protocol

import httpx

from app.common.logging import get_logger
from app.common.response import AppError
from app.config import settings

logger = get_logger(__name__)


class LLMResult(dict):
    """LLM 调用结果：{content, parsed, usage, latency_ms, model}。

    Accessors 提供类型友好的访问。
    """

    @property
    def content(self) -> str:
        return self.get("content", "")

    @property
    def parsed(self) -> Any:
        return self.get("parsed")

    @property
    def usage(self) -> dict:
        return self.get("usage", {})

    @property
    def latency_ms(self) -> int:
        return self.get("latency_ms", 0)

    @property
    def model(self) -> str:
        return self.get("model", "")


class LLMClient(Protocol):
    """LLM 客户端抽象。"""

    def chat(
        self,
        messages: list[dict[str, str]],
        schema: dict | None = None,
        model: str | None = None,
    ) -> LLMResult:
        ...


def digest_text(text: str) -> str:
    """输入/输出摘要：SHA256，截断，避免存明文。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def _retry_call(fn, max_retries: int | None = None) -> Any:
    max_retries = max_retries if max_retries is not None else settings.llm_max_retries
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning("llm_call_retry", attempt=attempt + 1, error=str(exc))
            time.sleep(min(2**attempt, 4))
    raise AppError(code=503, message=f"LLM 调用失败：{last_exc}", status_code=503)


class HuaweiClient:
    """华为云盘古大模型接入。

    生产环境通过 ModelArts / 盘古推理 API 调用，IAM AK/SK 鉴权。
    具体端点与模型版本由 settings.llm_huawei_endpoint / settings.llm_model 配置。
    """

    def chat(
        self,
        messages: list[dict[str, str]],
        schema: dict | None = None,
        model: str | None = None,
    ) -> LLMResult:
        model = model or settings.llm_model
        payload = {"model": model, "messages": messages, "stream": False}
        if schema:
            payload["response_format"] = {"type": "json_schema", "schema": schema}

        def _do() -> httpx.Response:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                return client.post(
                    settings.llm_huawei_endpoint,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Auth-Token": _build_auth_token(),
                    },
                )

        resp = _retry_call(_do)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = _safe_json(content) if schema else None
        return LLMResult(
            content=content,
            parsed=parsed,
            usage=data.get("usage", {}),
            latency_ms=int(data.get("latency_ms", 0)),
            model=model,
        )


def _build_auth_token() -> str:
    """构建华为云 IAM 鉴权 token（简化：直接用 AK/SK 占位，实际由 SDK 生成）。"""
    # 生产应使用 esdk-obs-python-sdk 或 huaweicloud-sdk-python3 生成签名
    return f"{settings.llm_huawei_ak}:{settings.llm_huawei_sk}"


def _safe_json(text: str) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


class MockClient:
    """测试/CI 用：基于规则的可复现 LLM 实现，无外部依赖。"""

    def __init__(self, responses: dict[str, Any] | None = None):
        self._responses = responses or {}

    def chat(
        self,
        messages: list[dict[str, str]],
        schema: dict | None = None,
        model: str | None = None,
    ) -> LLMResult:
        # 以最后一条用户消息内容的关键词路由到预设响应
        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        key = self._match_key(user_msg)
        payload = self._responses.get(key, {"_default": True})
        content = json.dumps(payload, ensure_ascii=False)
        return LLMResult(
            content=content,
            parsed=payload if schema else None,
            usage={"prompt_tokens": len(user_msg), "completion_tokens": len(content)},
            latency_ms=1,
            model=model or "mock-llm",
        )

    def with_response(self, key: str, payload: Any) -> "MockClient":
        self._responses[key] = payload
        return self

    def add_defaults(self) -> "MockClient":
        """补齐默认响应，使 MockClient 在未配置关键词时也能返回符合预期的输出。
        覆盖 JD 生成 / 简历分析 / 面试评价三个核心场景。
        """
        defaults: dict[str, Any] = {
            "岗位": {
                "jd": {"title": "默认岗位", "responsibilities": ["负责相关开发工作"], "requirements": ["本科及以上学历"]},
                "job_profile": {"方向": "通用", "年限": "3-5年"},
                "skill_requirements": ["团队协作", "沟通能力"],
                "rationale": "基于岗位名称与等级自动推导",
            },
            "简历": {
                "match_score": 75,
                "advantages": ["经验匹配"],
                "risks": ["无相关风险提示"],
                "rationale": {"hit": ["团队协作"], "miss": []},
            },
            "面试": {
                "summary": "候选人整体表现尚可",
                "capability_eval": {
                    "专业技能": "符合", "沟通表达": "良好",
                    "解决问题": "一般", "团队协作": "良好", "学习能力": "符合",
                },
                "recommendation": "推荐",
                "rationale": {"专业技能": "符合要求"},
            },
        }
        for k, v in defaults.items():
            self._responses.setdefault(k, v)
        return self

    @staticmethod
    def _match_key(text: str) -> str:
        # 顺序敏感：先匹配更具体的关键词，避免简历提示词中的"岗位"误命中岗位模板
        for kw in ("简历", "面试", "JD", "jd", "岗位"):
            if kw in text:
                return kw
        return "_default"


def get_llm_client() -> LLMClient:
    """按 settings.llm_provider 返回客户端实例。mock 模式下自动补齐默认响应。"""
    provider = settings.llm_provider.lower()
    if provider == "mock":
        return MockClient().add_defaults()
    if provider == "huawei":
        return HuaweiClient()
    raise AppError(code=500, message=f"未知 LLM provider: {provider}", status_code=500)
