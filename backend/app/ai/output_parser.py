"""AI 输出解析器：JSON Schema 校验 + rationale 抽取。对应 system-design 2.2。"""
from typing import Any

from app.common.response import AppError


def parse_json_object(content: str) -> dict[str, Any]:
    """将 LLM 返回内容解析为 dict；失败抛业务异常（由调用方决定重试/降级）。"""
    import json

    text = content.strip()
    # 容忍 markdown 代码块包裹
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AppError(code=502, message="AI 输出非合法 JSON", status_code=502) from exc
    if not isinstance(data, dict):
        raise AppError(code=502, message="AI 输出非对象结构", status_code=502)
    return data


def require_rationale(data: dict[str, Any]) -> Any:
    """强制要求可解释依据；缺失视为缺陷。"""
    if "rationale" not in data or data["rationale"] in (None, "", []):
        raise AppError(code=502, message="AI 输出缺少可解释依据 rationale", status_code=502)
    return data["rationale"]
