"""简历脱敏：送入 LLM 前剔除明文敏感信息。对应 PRD F5.5 / system-design 2.4。"""
import re

# 身份证号、手机号、邮箱、住址关键词
_ID_CARD = re.compile(r"\d{17}[\dXx]|\d{15}")
_PHONE = re.compile(r"1[3-9]\d{9}")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

_MASKED_TOKENS = ["身份证", "住址", "地址", "家庭住址", "现居"]


def mask_sensitive(text: str) -> str:
    """脱敏：替换敏感信息为占位符。"""
    if not text:
        return text
    text = _ID_CARD.sub("[ID_REDACTED]", text)
    text = _PHONE.sub("[PHONE_REDACTED]", text)
    text = _EMAIL.sub("[EMAIL_REDACTED]", text)
    return text


def contains_plaintext_pii(text: str) -> bool:
    """检查是否仍含明文身份证/手机（用于测试断言）。"""
    return bool(_ID_CARD.search(text) or _PHONE.search(text))
