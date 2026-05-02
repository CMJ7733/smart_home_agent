# TODO (Phase 1): RAG 检索节点（迁移自 rag/rag_service.py）
# 输入: AgentState.user_input
# 输出: AgentState.retrieved_context (list[str])
# Phase 1: 复用现有 Chroma + DashScope embedding 逻辑
# Phase 2: 替换为 Milvus 混合检索 + BGE-Reranker，接口不变

from app.agent.state import AgentState
from rag.vector_store import VectorStoreService


# 复用现有的 Chroma 向量库
_vector_store = VectorStoreService()


def rag_node(state: AgentState) -> AgentState:
    """RAG 检索节点: 从 Chroma 向量库检索相关文档"""
    user_input = state.get("user_input", "")
    retriever = _vector_store.get_retriever()
    docs = retriever.invoke(user_input)
    return {"retrieved_context": [doc.page_content for doc in docs]}
