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

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.models.schemas import ChatRequest, ChatResponse
from app.agent.graph import graph
from app.agent.state import AgentState

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """同步 REST 对话接口"""
    state: AgentState = {
        "session_id": request.session_id,
        "user_id": request.user_id,
        "user_input": request.message,
        "chat_history": [],
        "extracted_entities": {},
        "retrieved_context": [],
        "current_intent": "",
        "tool_calls": [],
        "final_response": "",
        "trace_id": f"trace-{request.session_id}",
    }

    result = graph.invoke(state)
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
                "chat_history": [],
                "extracted_entities": {},
                "retrieved_context": [],
                "current_intent": "",
                "tool_calls": [],
                "final_response": "",
                "trace_id": f"trace-{session_id}",
            }

            # 直接获取最终结果（简化版）
            result = graph.invoke(state)
            await websocket.send_json({
                "type": "final",
                "response": result.get("final_response", ""),
                "trace_id": result.get("trace_id", ""),
                "intent": result.get("current_intent", ""),
            })
    except WebSocketDisconnect:
        pass