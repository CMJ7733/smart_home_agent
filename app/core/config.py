# 统一配置入口，通过 pydantic-settings 从 .env 加载
# 替代现有分散的 config/*.yml 方式（YAML 配置仍保留作向量库参数）

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM Provider: "ollama" | "api"
    llm_provider: str = "ollama"

    # Ollama (local)
    ollama_base_url: str = "http://localhost:11434"
    chat_model_name: str = "qwen3.5:2b"
    embedding_model_name: str = "nomic-embed-text-v2-moe"

    # OpenAI-compatible API (any provider)
    api_base_url: str = "https://api.minimaxi.com/v1"        # e.g. https://api.deepseek.com/v1
    api_key: str = ""
    api_model_name: str = "minimax-m2.7"      # e.g. deepseek-chat

    # Embedding provider: "ollama" | "api" (独立于 llm_provider，默认用 ollama)
    embed_provider: str = "api"
    embed_model_name: str = "BAAI/bge-m3"
    embed_api_base_url: str = "https://api.siliconflow.cn/v1"
    embed_api_key: str = ""       # 独立的 embedding API key，为空时复用 api_key

    # Redis (Phase 2)
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 86400

    # LangSmith (Phase 3)
    langsmith_api_key: str = ""
    langsmith_project: str = "smart-home-agent"
    langchain_tracing_v2: bool = False

    # Milvus (Phase 2)
    milvus_uri: str = "http://localhost:19530"

    # Evaluation DB (Phase 3)
    eval_db_path: str = "data/eval_logs.db"

    # Huawei IoTDA (Phase IoTDA)
    iotda_endpoint: str = ""          # 应用侧 REST: "xxxxxx.st1.iotda-app.cn-north-4.myhuaweicloud.com" (无 https://)
    iotda_device_endpoint: str = ""   # 设备侧 MQTT: "xxxxxx.st1.iotda-device.cn-north-4.myhuaweicloud.com"
    iotda_project_id: str = ""
    iotda_ak: str = ""
    iotda_sk: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
