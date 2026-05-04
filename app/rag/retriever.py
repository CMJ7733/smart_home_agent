from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.config_handler import milvus_conf
from utils.path_tool import get_abs_path
from utils.file_handler import pdf_loader, txt_loader, listdir_with_allowed_type
from utils.logger_handler import logger

_TOP_K_BM25 = 20
_TOP_K_VECTOR = 20
_TOP_K_FINAL = 3


def _load_all_chunks() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=milvus_conf["chunk_size"],
        chunk_overlap=milvus_conf["chunk_overlap"],
        separators=milvus_conf["separators"],
    )
    chunks = []
    files = listdir_with_allowed_type(
        get_abs_path(milvus_conf["data_path"]),
        tuple(milvus_conf["allow_knowledge_file_type"]),
    )
    for path in files:
        try:
            docs = (
                txt_loader(path) if path.endswith("txt") else
                pdf_loader(path) if path.endswith("pdf") else []
            )
            chunks.extend(splitter.split_documents(docs))
        except Exception as e:
            logger.warning(f"[HybridRetriever] 加载文件失败: {path} — {e}")
    return chunks


class HybridRetriever:
    def __init__(self):
        from app.rag.vector_store import VectorStoreService
        self._vs = VectorStoreService()
        self._bm25: BM25Retriever | None = None
        self._reranker = None

    def _get_bm25(self) -> BM25Retriever:
        if self._bm25 is None:
            logger.info("[HybridRetriever] 初始化 BM25 索引...")
            chunks = _load_all_chunks()
            self._bm25 = BM25Retriever.from_documents(chunks, k=_TOP_K_BM25)
        return self._bm25

    def _get_reranker(self):
        if self._reranker is None:
            import os
            os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
            logger.info("[HybridRetriever] 加载 BGE-Reranker 模型（首次从 hf-mirror 下载）...")
            from FlagEmbedding import FlagReranker
            self._reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
        return self._reranker

    def retrieve(self, query: str) -> list[Document]:
        # 1. BM25 top-20
        bm25_docs = self._get_bm25().invoke(query)

        # 2. 向量检索 top-20
        vector_retriever = self._vs.vector_store.as_retriever(
            search_kwargs={"k": _TOP_K_VECTOR}
        )
        vector_docs = vector_retriever.invoke(query)

        # 3. 合并去重（以 page_content 前 80 字符为 key）
        seen: set[str] = set()
        candidates: list[Document] = []
        for doc in bm25_docs + vector_docs:
            key = doc.page_content[:80]
            if key not in seen:
                seen.add(key)
                candidates.append(doc)

        if len(candidates) <= _TOP_K_FINAL:
            return candidates

        # 4. BGE-Reranker 重排 → top-3
        try:
            reranker = self._get_reranker()
            pairs = [[query, doc.page_content] for doc in candidates]
            scores = reranker.compute_score(pairs, normalize=True)
            ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
            return [doc for _, doc in ranked[:_TOP_K_FINAL]]
        except Exception as e:
            logger.warning(f"[HybridRetriever] Reranker 失败，降级返回前 {_TOP_K_FINAL} 条: {e}")
            return candidates[:_TOP_K_FINAL]


_hybrid_retriever: HybridRetriever | None = None


def get_hybrid_retriever() -> HybridRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever
