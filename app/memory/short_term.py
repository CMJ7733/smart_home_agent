import json
import redis
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict


class ShortTermMemory:
    def __init__(self, redis_url: str, ttl: int = 86400):
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.ttl = ttl

    def load(self, session_id: str) -> list[BaseMessage]:
        raw = self.client.get(self._key(session_id))
        if not raw:
            return []
        try:
            return messages_from_dict(json.loads(raw))
        except (json.JSONDecodeError, TypeError, ValueError):
            return []

    def save(self, session_id: str, messages: list[BaseMessage]) -> None:
        payload = json.dumps(messages_to_dict(messages), ensure_ascii=False)
        self.client.setex(self._key(session_id), self.ttl, payload)

    @staticmethod
    def _key(session_id: str) -> str:
        if not session_id:
            raise ValueError("session_id is required")
        return f"chat:{session_id}"
