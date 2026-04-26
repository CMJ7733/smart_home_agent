# TODO (Phase 3): 评估日志数据模型（对应 SQLite/PostgreSQL 表结构）
# 每次完整对话落一条记录，供 RAGAS 评估 + Bad Case 筛选使用

from pydantic import BaseModel
from typing import Optional


class AgentTrajectoryStep(BaseModel):
    node: str
    detail: dict       # e.g. {"intent": "device_control"} 或 {"action": "set_temp", "args": {...}}


class EvalLog(BaseModel):
    trace_id: str
    user_id: str
    query: str
    agent_trajectory: list[AgentTrajectoryStep]
    response: str
    user_feedback: Optional[int] = None   # 1=赞, -1=踩, None=未反馈
    eval_metrics: Optional[dict] = None   # RAGAS 离线打分结果
    # {
    #   "context_relevance": 0.95,
    #   "faithfulness": 0.88,
    #   "intent_accuracy": 1.0,
    #   "tool_call_correctness": 1.0
    # }
