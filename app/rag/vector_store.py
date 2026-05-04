from datetime import datetime
from langchain_milvus import Milvus
from langchain_core.documents import Document
from app.core.config import get_settings
from utils.config_handler import milvus_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.file_handler import pdf_loader, txt_loader, listdir_with_allowed_type, get_file_md5_hex
from utils.logger_handler import logger
import os

_DEVICE_TYPE_KEYWORDS = {
    "扫地": "vacuum",
    "扫拖": "vacuum",
    "故障": "vacuum",
    "维护": "vacuum",
    "保养": "vacuum",
    "选购": "vacuum",
}


def _infer_device_type(filename: str) -> str:
    for keyword, device_type in _DEVICE_TYPE_KEYWORDS.items():
        if keyword in filename:
            return device_type
    return "appliance"


class VectorStoreService:
    def __init__(self):
        settings = get_settings()
        from pymilvus import connections
        from urllib.parse import urlparse
        parsed = urlparse(settings.milvus_uri)
        host = parsed.hostname or "localhost"
        port = str(parsed.port or 19530)
        if not connections.has_connection("default"):
            connections.connect(alias="default", host=host, port=port)
        self.vector_store = Milvus(
            embedding_function=embed_model,
            collection_name=milvus_conf["collection_name"],
            connection_args={"host": host, "port": port},
            auto_id=True,
            enable_dynamic_field=True,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=milvus_conf["chunk_size"],
            chunk_overlap=milvus_conf["chunk_overlap"],
            separators=milvus_conf["separators"],
            length_function=len,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": milvus_conf["k"]})

    def load_document(self):
        md5_store = get_abs_path(milvus_conf["md5_hex_store"])

        def check_md5(md5: str) -> bool:
            if not os.path.exists(md5_store):
                open(md5_store, "w", encoding="utf-8").close()
                return False
            with open(md5_store, "r", encoding="utf-8") as f:
                return any(line.strip() == md5 for line in f)

        def save_md5(md5: str):
            with open(md5_store, "a", encoding="utf-8") as f:
                f.write(md5 + "\n")

        allowed_files = listdir_with_allowed_type(
            get_abs_path(milvus_conf["data_path"]),
            tuple(milvus_conf["allow_knowledge_file_type"]),
        )

        for path in allowed_files:
            md5 = get_file_md5_hex(path)
            if check_md5(md5):
                logger.info(f"[Milvus] 已存在，跳过: {path}")
                continue

            try:
                docs: list[Document] = (
                    txt_loader(path) if path.endswith("txt") else
                    pdf_loader(path) if path.endswith("pdf") else []
                )
                if not docs:
                    logger.warning(f"[Milvus] 无有效内容，跳过: {path}")
                    continue

                filename = os.path.basename(path)
                device_type = _infer_device_type(filename)
                updated_at = datetime.now().isoformat()
                for doc in docs:
                    doc.metadata = {
                        "device_type": device_type,
                        "source_file": filename,
                        "updated_at": updated_at,
                    }

                chunks = self.splitter.split_documents(docs)
                if not chunks:
                    logger.warning(f"[Milvus] 分片为空，跳过: {path}")
                    continue

                self.vector_store.add_documents(chunks)
                save_md5(md5)
                logger.info(f"[Milvus] 加载成功: {path} ({len(chunks)} chunks)")
            except Exception as e:
                logger.error(f"[Milvus] 加载失败: {path} — {e}", exc_info=True)
