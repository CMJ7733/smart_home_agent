# TODO (Phase 1): Pydantic 请求/响应模型
# 供 FastAPI 接口 (app/api/endpoints.py) 使用

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    trace_id: str
    intent: Optional[str] = None


class FeedbackRequest(BaseModel):
    trace_id: str
    rating: int        # 1 = 赞，-1 = 踩
    comment: Optional[str] = None


class MemoryUpdateRequest(BaseModel):
    preferences: dict  # e.g. {"bedroom_temp_preference": 24}
