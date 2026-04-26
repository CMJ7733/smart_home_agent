# Phase 1: 复用现有 rag/vector_store.py（Chroma + DashScope embedding）
# Phase 2: 重写为 Milvus 实现，对外接口保持不变（依赖倒置）
#
# 统一接口契约（两个 Phase 均需实现）:
#   get_retriever() -> BaseRetriever
#   load_document() -> None

# TODO (Phase 1): 将 rag/vector_store.py 中的 VectorStoreService 迁移至此
# TODO (Phase 2): 替换底层实现为 pymilvus / langchain-milvus，增加 device_type / source_file 标量字段
