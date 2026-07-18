"""数据分析 schema。对应 F4 / T8。"""
from datetime import date

from pydantic import BaseModel


class AnalyticsOverviewQuery(BaseModel):
    start: date | None = None
    end: date | None = None


class AnalyticsOverview(BaseModel):
    recruitment_cycle_days: float | None   # 招聘周期（平均天数）
    conversion_rate: dict                   # 漏斗转化率：各阶段
    channel_effectiveness: dict              # 渠道效果（MVP：按创建来源占位统计）
    total_jobs: int
    total_resumes: int
    total_interviews: int
