# TODO (Phase 1): RAG 检索节点（迁移自 rag/rag_service.py）
# 输入: AgentState.user_input
# 输出: AgentState.retrieved_context (list[str])
# Phase 1: 复用现有 Chroma + DashScope embedding 逻辑
# Phase 2: 替换为 Milvus 混合检索 + BGE-Reranker，接口不变

from app.agent.state import AgentState


def rag_node(state: AgentState) -> AgentState:
    raise NotImplementedError("Phase 1: 待实现 RAG 检索节点")
