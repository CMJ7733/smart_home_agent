# TODO (Phase 2): 记忆写入节点（每条路径末尾异步触发）
# 短期记忆: 将本轮对话追加到 Redis（key: chat:{session_id}, TTL 24h）
# 长期记忆: 触发后台任务，LLM 抽取用户偏好并写入 Milvus（Phase 2）
# Phase 1 占位: 仅写 Redis 短期记忆

from app.agent.state import AgentState


def memory_writer_node(state: AgentState) -> AgentState:
    raise NotImplementedError("Phase 2: 待实现记忆写入节点")
