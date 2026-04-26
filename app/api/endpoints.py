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

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}

# TODO: 其余接口在 Phase 1-3 逐步实现
