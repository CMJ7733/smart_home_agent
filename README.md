# Smart Home Agent

An enterprise-oriented smart home agent built with LangGraph, hybrid RAG, and an LLMOps evaluation loop. Supports natural language device control, knowledge base Q&A, scene automation, and persistent user memory.

## Architecture

```
User → FastAPI → LangGraph StateGraph
                      │
              [router] ─────────────────────────────────────────┐
                 │                                               │
         ┌───────┼──────────────┬──────────────┐                │
         ▼       ▼              ▼              ▼                │
      [chat]  [rag_node]  [entity_extractor]  [scene_planner]  report→END
         │    [responder]  [tool_caller]       [tool_caller]
         │         │        [responder]        [responder]
         └─────────┴────────────┴──────────────┘
                              │
                     [memory_writer] → END
```

**Intent routing:** `chitchat` | `kb_query` | `device_control` | `scene` | `report`

## Stack

| Layer | Component |
|---|---|
| Orchestration | LangGraph StateGraph |
| LLM | MiniMax `minimax-m2.7` (via OpenAI-compatible API) |
| Embeddings | SiliconFlow `BAAI/bge-m3` (1024-dim, batch ≤ 64) |
| Vector Store | Milvus (standalone, via Docker) |
| Hybrid Retrieval | BM25 + Milvus vector + BGE-Reranker |
| Short-term Memory | Redis (session chat history, TTL 24h) |
| Long-term Memory | Milvus `user_preferences` collection |
| API | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Evaluation | RAGAS + SQLite eval log + LangSmith (optional) |

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys:
#   API_KEY=<your MiniMax key>
#   EMBED_API_KEY=<your SiliconFlow key>
#   LLM_PROVIDER=api
#   EMBED_PROVIDER=api
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start infrastructure (Redis + Milvus)

```bash
docker compose up -d
```

### 4. Load the knowledge base

```bash
python -c "from app.rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

### 5. Start the API server

```bash
uvicorn app.main:app --reload
```

### 6. Start the Streamlit frontend

```bash
streamlit run streamlit_app.py
```

The Streamlit app connects to `http://localhost:8000/api/v1` and provides a chat UI with intent details, feedback buttons, an evaluation dashboard, and an eval log viewer.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `api` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `CHAT_MODEL_NAME` | `qwen3.5:2b` | Ollama chat model |
| `API_BASE_URL` | `https://api.minimaxi.com/v1` | OpenAI-compatible API base |
| `API_KEY` | *(required if api)* | LLM API key |
| `API_MODEL_NAME` | `minimax-m2.7` | LLM model name |
| `EMBED_PROVIDER` | `ollama` | `ollama` or `api` |
| `EMBED_MODEL_NAME` | `BAAI/bge-m3` | Embedding model name |
| `EMBED_API_BASE_URL` | `https://api.siliconflow.cn/v1` | Embedding API base (no trailing path) |
| `EMBED_API_KEY` | *(required if api)* | Embedding API key |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `MILVUS_URI` | `http://localhost:19530` | Milvus server URI |
| `LANGSMITH_API_KEY` | *(optional)* | Enable LangSmith tracing |
| `LANGCHAIN_TRACING_V2` | `false` | Set `true` to enable tracing |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/chat` | Send a message, returns `response`, `trace_id`, `intent` |
| `POST` | `/api/v1/feedback` | Submit thumbs up/down for a trace |
| `GET` | `/api/v1/eval/dashboard` | Aggregated evaluation metrics |

## Project Layout

```
app/
  agent/
    graph.py              LangGraph StateGraph definition
    state.py              AgentState TypedDict
    nodes/
      router.py           Intent classification
      chat_node.py        Chitchat via LLM
      rag_node.py         Hybrid retrieval (BM25 + Milvus + Reranker)
      entity_extractor.py Extract device/action entities from user input
      tool_caller.py      Execute device/scene API calls
      scene_planner.py    Map scene names to device action plans
      responder.py        Assemble final natural-language response
      memory_writer.py    Persist turn to short- and long-term memory
  api/
    endpoints.py          FastAPI routes
  core/
    config.py             pydantic-settings configuration
  db/
    eval_log_repo.py      SQLite eval log CRUD
  evaluation/
    run_ragas_eval.py     RAGAS evaluation runner
  memory/
    short_term.py         Redis session memory
    memory_graph.py       Milvus long-term user preference memory
  rag/
    vector_store.py       Milvus collection management + document loading
    retriever.py          Hybrid BM25 + vector retrieval + BGE-Reranker
  tools/
    device_api.py         Smart home device control stubs
    scene_api.py          Scene execution stubs
model/
  factory.py              ChatModel / Embeddings factory (Ollama or API)
prompts/                  Prompt templates
data/                     Knowledge base documents + eval_logs.db
streamlit_app.py          Streamlit debug/demo frontend
docker-compose.yml        Redis + Milvus (etcd + MinIO) stack
```

## Notes

- `minimax-m2.7` is a reasoning model that emits `<think>...</think>` blocks. The pipeline strips these automatically before returning responses.
- SiliconFlow's embedding API enforces a batch limit of 64 items. The `chunk_size=64` parameter in the embeddings factory handles this.
- Milvus collections are dimension-specific. If you switch embedding models (e.g., from 768-dim Ollama to 1024-dim bge-m3), drop and rebuild the collections.
- Long-term memory stores user device preferences in a Milvus `user_preferences` collection and is updated after every conversation turn.
