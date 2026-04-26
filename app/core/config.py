# 统一配置入口，通过 pydantic-settings 从 .env 加载
# 替代现有分散的 config/*.yml 方式（YAML 配置仍保留作向量库参数）

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DashScope / Qwen
    dashscope_api_key: str = ""
    chat_model_name: str = "qwen3-max"
    embedding_model_name: str = "text-embedding-v4"

    # Redis (Phase 2)
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 86400

    # LangSmith (Phase 3)
    langsmith_api_key: str = ""
    langsmith_project: str = "smart-home-agent"
    langchain_tracing_v2: bool = False

    # Milvus (Phase 2)
    milvus_uri: str = "http://localhost:19530"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
