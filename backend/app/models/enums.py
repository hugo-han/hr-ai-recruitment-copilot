"""用户与角色定义。

角色：HR / HR_LEAD / INTERVIEWER / ADMIN
对应 PRD 第二章用户角色与 F5.1 角色权限。
"""
from enum import StrEnum


class Role(StrEnum):
    HR = "HR"                  # 招聘专员：JD、简历筛选
    HR_LEAD = "HR_LEAD"        # 招聘负责人：看板、策略
    INTERVIEWER = "INTERVIEWER"  # 面试官：面试记录与评价
    ADMIN = "ADMIN"            # 系统管理员：权限、配置、删除/导出


# 角色可见的功能域（粗粒度，细粒度由接口层校验）
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.HR: {"job", "resume", "interview"},
    Role.HR_LEAD: {"job", "resume", "interview", "analytics"},
    Role.INTERVIEWER: {"interview"},
    Role.ADMIN: {"job", "resume", "interview", "analytics", "user", "audit", "dictionary"},
}
