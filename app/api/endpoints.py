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
import json
import asyncio
from collections import defaultdict
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


def _write_eval_log_task(result: dict, request: ChatRequest):
    try:
        from app.db.eval_log_repo import EvalLogRepo
        EvalLogRepo().save(
            trace_id=result.get("trace_id", ""),
            user_id=request.user_id,
            query=request.message,
            intent=result.get("current_intent", ""),
            response=result.get("final_response", ""),
            contexts=result.get("retrieved_context", []),
            trajectory=result.get("tool_calls", []),
        )
    except Exception:
        pass


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
    background_tasks.add_task(_write_eval_log_task, result, request)

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

            # Trigger preference extraction and eval log writing (fire-and-forget)
            asyncio.create_task(_extract_preferences_task(user_id, state["chat_history"]))
            chat_req = ChatRequest(message=user_input, session_id=session_id, user_id=user_id)
            asyncio.create_task(_write_eval_log_task(result, chat_req))
    except WebSocketDisconnect:
        pass


@router.post("/feedback")
async def submit_feedback(trace_id: str, feedback: int):
    """用户反馈：feedback=1 赞，feedback=-1 踩"""
    from app.db.eval_log_repo import EvalLogRepo
    EvalLogRepo().update_feedback(trace_id, feedback)
    return {"status": "ok"}


@router.get("/eval/dashboard")
async def eval_dashboard(days: int = 7):
    """评估看板：最近 N 天的 RAGAS 指标聚合"""
    from app.db.eval_log_repo import EvalLogRepo
    logs = EvalLogRepo().query_recent(days)

    daily: dict[str, list] = defaultdict(list)
    for log in logs:
        day = log["created_at"][:10]
        if log["eval_metrics_json"]:
            try:
                daily[day].append(json.loads(log["eval_metrics_json"]))
            except Exception:
                pass

    metric_keys = ["faithfulness", "answer_relevancy", "context_precision"]
    daily_metrics = {}
    for day, metrics in daily.items():
        if metrics:
            daily_metrics[day] = {
                k: round(sum(m.get(k, 0) for m in metrics) / len(metrics), 3)
                for k in metric_keys
            }

    return {
        "total_turns": len(logs),
        "days": days,
        "daily_metrics": daily_metrics,
        "bad_case_count": sum(1 for l in logs if l["eval_metrics_json"]),
        "feedback_stats": {
            "thumbs_up": sum(1 for l in logs if l["user_feedback"] == 1),
            "thumbs_down": sum(1 for l in logs if l["user_feedback"] == -1),
        },
    }