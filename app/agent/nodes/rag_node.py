# TODO (Phase 1): RAG 检索节点（迁移自 rag/rag_service.py）
# 输入: AgentState.user_input
# 输出: AgentState.retrieved_context (list[str])
# Phase 1: 复用现有 Chroma + DashScope embedding 逻辑
# Phase 2: 替换为 Milvus 混合检索 + BGE-Reranker，接口不变

from app.agent.state import AgentState
from app.rag.retriever import get_hybrid_retriever


def rag_node(state: AgentState) -> AgentState:
    """RAG 检索节点: BM25 + 向量混合检索，BGE-Reranker 重排，返回 top-3"""
    user_input = state.get("user_input", "")
    docs = get_hybrid_retriever().retrieve(user_input)
    return {"retrieved_context": [doc.page_content for doc in docs]}
