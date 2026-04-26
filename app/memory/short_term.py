# TODO (Phase 2): Redis 短期记忆
# key schema: chat:{session_id}   value: JSON list of messages   TTL: 86400s (24h)
# 操作:
#   load(session_id) -> list[BaseMessage]   在 LangGraph 节点入口调用
#   save(session_id, messages) -> None      在 LangGraph 节点出口调用

import redis
from langchain_core.messages import BaseMessage


class ShortTermMemory:
    def __init__(self, redis_url: str, ttl: int = 86400):
        raise NotImplementedError("Phase 2: 待实现 Redis 短期记忆")

    def load(self, session_id: str) -> list[BaseMessage]:
        raise NotImplementedError("Phase 2: 待实现")

    def save(self, session_id: str, messages: list[BaseMessage]) -> None:
        raise NotImplementedError("Phase 2: 待实现")
