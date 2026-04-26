# TODO (Phase 2): 混合检索 + BGE-Reranker
# Phase 1: 直接使用 vector_store.get_retriever()（纯向量，k=3）
# Phase 2 实现步骤:
#   1. BM25 检索（rank_bm25 或 Milvus 稀疏向量）→ top-20 候选
#   2. 向量检索（DashScope text-embedding-v4）→ top-20 候选
#   3. 结果合并去重
#   4. BGE-Reranker（bge-reranker-v2-m3）二次重排 → top-3
#   5. 返回给 rag_node.py

from langchain_core.retrievers import BaseRetriever


def get_hybrid_retriever() -> BaseRetriever:
    raise NotImplementedError("Phase 2: 待实现混合检索 + Reranker")
