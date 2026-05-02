# Smart Home Agent

An enterprise-oriented smart home agent project built around LangGraph, RAG, and an LLMOps evaluation loop.

## Stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph |
| LLM | Ollama `gemma4:e4b` |
| Embeddings | Ollama `nomic-embed-text-v2-moe` |
| Vector Store (Phase 1) | Chroma |
| Memory (Phase 2) | Redis |
| API | FastAPI + WebSocket |
| Evaluation (Phase 3) | LangSmith + RAGAS |

## Quick Start

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Make sure Ollama is running locally and pull the required models:

```bash
ollama pull gemma4:e4b
ollama pull nomic-embed-text-v2-moe
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start Redis:

```bash
docker compose up -d
```

5. Load the knowledge base:

```bash
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

6. Run the current Streamlit app:

```bash
streamlit run app.py
```

## Current Model Config

Environment variables:

- `OLLAMA_BASE_URL`
- `CHAT_MODEL_NAME`
- `EMBEDDING_MODEL_NAME`

Defaults:

- chat model: `gemma4:e4b`
- embedding model: `nomic-embed-text-v2-moe`
- Ollama URL: `http://localhost:11434`

## Project Layout

```text
app/                new architecture workspace
agent/              legacy ReAct agent
rag/                current Chroma-based RAG implementation
data/               knowledge base files
streamlit_debug/    future debug client
tests/              test package
```
