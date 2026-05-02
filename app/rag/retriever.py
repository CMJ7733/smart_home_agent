# TODO (Phase 2): hybrid retrieval + BGE reranker
#
# Phase 1:
#   reuse `vector_store.get_retriever()` and keep the current `k=3` setup.
#
# Phase 2 plan:
#   1. BM25 retrieval (`rank_bm25` or Milvus sparse vectors) -> top-20 candidates
#   2. Vector retrieval with Ollama embeddings (`nomic-embed-text-v2-moe`) -> top-20 candidates
#   3. Merge and deduplicate candidates
#   4. Rerank with `bge-reranker-v2-m3` -> top-3
#   5. Integrate into `rag_node.py`

from langchain_core.retrievers import BaseRetriever


def get_hybrid_retriever() -> BaseRetriever:
    raise NotImplementedError("Phase 2: hybrid retrieval + reranker is not implemented yet.")
