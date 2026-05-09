# Phase 2: 长期记忆 / 用户偏好图谱
# 会话结束后由 FastAPI BackgroundTask 异步触发
# 流程:
#   1. 输入本轮 chat_history
#   2. LLM 抽取结构化偏好: {room_temp_preference, light_color_preference, ...}
#   3. 写入 Milvus 独立 collection（user_preferences），标量索引 user_id
#   4. entity_extractor_node 遇到模糊指代时调用 query_preferences(user_id) 补全

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.documents import Document
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from langchain_milvus import Milvus

from model.factory import chat_model, embed_model
from utils.config_handler import milvus_conf
from utils.logger_handler import logger

_PREF_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "preference_extract_prompt.txt"
_COLLECTION_NAME = milvus_conf.get("user_preferences_collection_name", "user_preferences")
_EMBED_DIM = 1024  # nomic-embed-text-v2-moe output dimension


def _load_pref_prompt() -> str:
    with open(_PREF_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _get_milvus_connection():
    from app.core.config import get_settings
    from urllib.parse import urlparse
    settings = get_settings()
    parsed = urlparse(settings.milvus_uri)
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 19530)
    if not connections.has_connection("default"):
        connections.connect(alias="default", host=host, port=port)
    return host, port


def _ensure_collection_exists():
    """Create user_preferences collection with schema + indexes if it does not exist."""
    if utility.has_collection(_COLLECTION_NAME, using="default"):
        return

    schema = CollectionSchema(
        fields=[
            FieldSchema(name="preference_id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="preference_vector", dtype=DataType.FLOAT_VECTOR, dim=_EMBED_DIM),
        ],
        description="User long-term preferences",
        enable_dynamic_field=True,
    )
    collection = Collection(name=_COLLECTION_NAME, schema=schema, using="default")

    # Scalar index on user_id (VARCHAR use INVERTED index)
    collection.create_index("user_id", {"index_type": "INVERTED", "field": "user_id"})

    # Vector index
    collection.create_index(
        "preference_vector",
        {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}}
    )

    collection.flush()
    logger.info(f"[MemoryGraph] Created Milvus collection '{_COLLECTION_NAME}'")


def _build_vectorstore(host: str, port: str) -> Milvus:
    return Milvus(
        embedding_function=embed_model,
        collection_name=_COLLECTION_NAME,
        connection_args={"host": host, "port": port},
        vector_field="preference_vector",
        auto_id=True,
        enable_dynamic_field=True,
    )


class MemoryGraph:
    def __init__(self):
        host, port = _get_milvus_connection()
        _ensure_collection_exists()
        Collection(_COLLECTION_NAME, using="default").load()
        self._host = host
        self._port = port
        self._vs: Milvus | None = None

    @property
    def _vectorstore(self) -> Milvus:
        if self._vs is None:
            self._vs = _build_vectorstore(self._host, self._port)
        return self._vs

    def extract_and_save(self, user_id: str, chat_history: list) -> None:
        """
        Extract structured preferences from chat_history using LLM,
        then upsert into Milvus user_preferences collection (one doc per user).
        Called by FastAPI BackgroundTask after each turn.
        """
        if not user_id or not chat_history:
            return

        try:
            # 1. Build chat history text for the prompt (last 10 turns)
            history_text = "\n".join(
                f"用户: {m.content}"
                if (hasattr(m, "type") and m.type == "human")
                else f"助手: {m.content}"
                for m in chat_history[-10:]
            )

            # 2. LLM extraction
            prompt_template = _load_pref_prompt()
            prompt = prompt_template.replace("{chat_history_text}", history_text)
            messages = [{"role": "user", "content": prompt}]
            response = chat_model.invoke(messages)

            # 3. Parse JSON from LLM response
            content = response.content.strip()
            # 剥掉 reasoning model 的 <think>...</think> 块
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            # 兼容 markdown 代码块
            if content.startswith("```"):
                parts = content.split("```")
                content = parts[1] if len(parts) > 1 else content
                content = re.sub(r"^[a-zA-Z]+\n", "", content, count=1)
                content = content.strip()
            # 容错：定位首个 '{' 作为 JSON 起点
            brace = content.find("{")
            if brace > 0:
                content = content[brace:]
            try:
                decoder = json.JSONDecoder()
                raw, _ = decoder.raw_decode(content)
            except ValueError:
                logger.warning(f"[MemoryGraph] LLM response did not contain valid JSON: {response.content[:200]}")
                return

            # 4. Inject metadata
            raw["updated_at"] = datetime.now(timezone.utc).isoformat()

            # 5. Serialize scene_preferences if dict
            if isinstance(raw.get("scene_preferences"), dict):
                raw["scene_preferences"] = json.dumps(raw["scene_preferences"], ensure_ascii=False)

            # 6. Build document for Milvus
            doc = Document(
                page_content=json.dumps(raw, ensure_ascii=False),
                metadata={"user_id": user_id},
            )

            # 7. Upsert: delete existing doc(s) for this user, then add new one
            collection = Collection(_COLLECTION_NAME, using="default")
            expr = f'user_id == "{user_id}"'
            collection.delete(expr)
            self._vectorstore.add_documents([doc])
            collection.flush()
            logger.info(f"[MemoryGraph] Upserted preferences for user={user_id}")

        except Exception as e:
            logger.error(f"[MemoryGraph] extract_and_save failed for user={user_id}: {e}", exc_info=True)

    def query_preferences(self, user_id: str) -> dict:
        """
        Retrieve latest preference dict for user_id from Milvus.
        Uses filtered query on user_id index.
        Returns {} if no record found.
        """
        if not user_id:
            return {}

        try:
            collection = Collection(_COLLECTION_NAME, using="default")
            expr = f'user_id == "{user_id}"'
            results = collection.query(
                expr,
                output_fields=["*"],
                limit=1,
            )

            if not results:
                return {}

            record = results[0]
            record.pop("preference_vector", None)
            record.pop("preference_id", None)

            # Parse scene_preferences back to dict
            sp = record.get("scene_preferences", "{}")
            if sp and sp != "{}":
                try:
                    record["scene_preferences"] = json.loads(sp)
                except json.JSONDecodeError:
                    pass
            else:
                record["scene_preferences"] = {}

            return record

        except Exception as e:
            logger.error(f"[MemoryGraph] query_preferences failed for user={user_id}: {e}", exc_info=True)
            return {}


_memory_graph: MemoryGraph | None = None


def get_memory_graph() -> MemoryGraph:
    global _memory_graph
    if _memory_graph is None:
        _memory_graph = MemoryGraph()
    return _memory_graph
