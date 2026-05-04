# TODO (Phase 1): FastAPI 路由定义
#
# 接口清单:
#   GET  /api/v1/health                           健康检查
#   POST /api/v1/chat                             同步对话（REST）
#   WS   /api/v1/chat/stream/{session_id}         流式对话（WebSocket，逐节点推送状态）
#   GET  /api/v1/memory/{user_id}                 获取用户长期偏好（Phase 2）
#   PUT  /api/v1/memory/{user_id}                 更新用户偏好（Phase 2）
#   POST /api/v1/feedback                         用户反馈（Phase 3）
#   GET  /api/v1/eval/dashboard                   评估看板（Phase 3）

import uuid
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from app.models.schemas import ChatRequest, ChatResponse
from app.agent.graph import graph
from app.agent.state import AgentState
from app.memory.short_term import ShortTermMemory
from app.memory.memory_graph import get_memory_graph
from app.core.config import get_settings

router = APIRouter()
_memory = ShortTermMemory(redis_url=get_settings().redis_url, ttl=get_settings().redis_ttl)


def _extract_preferences_task(user_id: str, chat_history: list):
    """Fire-and-forget background task — failures are logged inside extract_and_save."""
    get_memory_graph().extract_and_save(user_id, chat_history)


def _load_history(session_id: str) -> list:
    try:
        return _memory.load(session_id)
    except Exception:
        return []


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    """同步 REST 对话接口"""
    state: AgentState = {
        "session_id": request.session_id,
        "user_id": request.user_id,
        "user_input": request.message,
        "chat_history": _load_history(request.session_id),
        "extracted_entities": {},
        "retrieved_context": [],
        "current_intent": "",
        "tool_calls": [],
        "final_response": "",
        "trace_id": str(uuid.uuid4()),
    }

    result = await graph.ainvoke(state)

    # Schedule preference extraction AFTER this turn completes (fire-and-forget)
    background_tasks.add_task(_extract_preferences_task, request.user_id, state["chat_history"])

    return ChatResponse(
        session_id=request.session_id,
        response=result.get("final_response", ""),
        trace_id=result.get("trace_id", ""),
        intent=result.get("current_intent", ""),
    )


@router.websocket("/chat/stream/{session_id}")
async def chat_stream(websocket: WebSocket, session_id: str):
    """WebSocket 流式对话接口，逐节点推送状态"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            user_input = data.get("message", "")
            user_id = data.get("user_id", "unknown")

            state: AgentState = {
                "session_id": session_id,
                "user_id": user_id,
                "user_input": user_input,
                "chat_history": _load_history(session_id),
                "extracted_entities": {},
                "retrieved_context": [],
                "current_intent": "",
                "tool_calls": [],
                "final_response": "",
                "trace_id": str(uuid.uuid4()),
            }

            result = await graph.ainvoke(state)
            await websocket.send_json({
                "type": "final",
                "response": result.get("final_response", ""),
                "trace_id": result.get("trace_id", ""),
                "intent": result.get("current_intent", ""),
            })

            # Trigger preference extraction after every turn (fire-and-forget)
            asyncio.create_task(_extract_preferences_task(user_id, state["chat_history"]))
    except WebSocketDisconnect:
        pass