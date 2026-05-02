# Phase 1: reuse the current `rag/vector_store.py` implementation (Chroma + Ollama embeddings)
# Phase 2: replace the backend with Milvus while keeping the same public interface.
#
# Public API target:
#   get_retriever() -> BaseRetriever
#   load_document() -> None
#
# TODO (Phase 1): move `VectorStoreService` from `rag/vector_store.py` into this module.
# TODO (Phase 2): switch the backend to `pymilvus` / `langchain-milvus`
# and add scalar fields such as `device_type` and `source_file`.
