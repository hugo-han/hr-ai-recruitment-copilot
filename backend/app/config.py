"""应用配置：从环境变量加载，密钥不入库。"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 应用
    app_name: str = "hr-ai-recruitment-copilot"
    app_env: str = "dev"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = "change-me-in-prod"

    # 数据库
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hr_copilot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # 对象存储 OBS
    obs_access_key: str = ""
    obs_secret_key: str = ""
    obs_endpoint: str = ""
    obs_bucket: str = "hr-copilot-resume"

    # LLM
    llm_provider: str = Field("huawei", description="huawei / mock")
    llm_huawei_ak: str = ""
    llm_huawei_sk: str = ""
    llm_huawei_endpoint: str = ""
    llm_huawei_region: str = "cn-north-4"
    llm_model: str = "pangu-default"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 3


@lru_cache
def get_settings() -> Settings:
    """单例配置，避免重复读取环境变量。"""
    return Settings()


settings = get_settings()
