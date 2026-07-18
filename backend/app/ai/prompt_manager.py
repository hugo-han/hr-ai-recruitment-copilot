"""提示词管理：版本化模板。对应 system-design 2.2。

MVP：内置默认模板，落库可后续扩展。每个 Agent 的提示词带 version 便于审计回滚。
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    system: str
    user_template: str  # 含 {placeholders}


# ===== 职位助手 =====
JOB_DRAFT_PROMPT = PromptTemplate(
    name="job_draft",
    version="v1",
    system=(
        "你是资深招聘 JD 撰写专家。根据岗位信息生成结构化 JD、岗位画像与技能要求。"
        "必须返回 JSON，包含字段 jd、job_profile、skill_requirements、rationale。"
        "rationale 说明生成依据。"
    ),
    user_template=(
        "岗位名称：{title}\n岗位等级：{level}\n业务要求：{business_req}\n"
        "请生成结构化结果。"
    ),
)


# ===== 简历分析助手 =====
RESUME_ANALYZE_PROMPT = PromptTemplate(
    name="resume_analyze",
    version="v1",
    system=(
        "你是资深简历评估专家。根据候选人简历与目标岗位画像，给出匹配评分、优势、风险与依据。"
        "必须返回 JSON，包含 match_score(0-100整数)、advantages(list)、risks(list)、rationale(含命中/缺失项)。"
        "不得在输出中泄露明文身份证号、手机号、住址。"
    ),
    user_template=(
        "目标岗位画像：{job_profile}\n岗位技能要求：{skill_requirements}\n"
        "候选人简历（已脱敏）：{resume_text}\n请输出评估结果。"
    ),
)


# ===== 面试助手 =====
INTERVIEW_EVAL_PROMPT = PromptTemplate(
    name="interview_eval",
    version="v1",
    system=(
        "你是资深面试评估专家。根据面试记录与岗位能力维度模板，生成面试总结、能力评价与推荐建议。"
        "必须返回 JSON，包含 summary、capability_eval(按维度)、recommendation(推荐/待定/不推荐)、rationale。"
    ),
    user_template=(
        "岗位能力维度模板：{competency_template}\n面试记录：{record_text}\n请输出评估结果。"
    ),
)


# ===== 面试助手（问题建议）=====
SUGGEST_QUESTIONS_PROMPT = PromptTemplate(
    name="suggest_questions",
    version="v1",
    system=(
        "你是资深面试官。根据岗位信息与能力维度模板，生成针对性面试问题建议。"
        "必须返回 JSON，包含 questions(list of {dimension, question})、rationale。"
        "每个维度至少 1 个问题，总数建议 5-10 个。"
    ),
    user_template=(
        "岗位画像：{job_profile}\n技能要求：{skill_requirements}\n能力维度：{competency_template}\n"
        "请生成面试问题建议。"
    ),
)


REGISTRY: dict[str, PromptTemplate] = {
    "job_draft": JOB_DRAFT_PROMPT,
    "resume_analyze": RESUME_ANALYZE_PROMPT,
    "interview_eval": INTERVIEW_EVAL_PROMPT,
    "suggest_questions": SUGGEST_QUESTIONS_PROMPT,
}


def get_prompt(name: str) -> PromptTemplate:
    if name not in REGISTRY:
        raise KeyError(f"未注册的提示词模板: {name}")
    return REGISTRY[name]
