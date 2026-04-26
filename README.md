# 智能家居 Agent

企业级多智能体家居控制系统，基于 LangGraph 状态机 + LLMOps 数据飞轮。

## 架构概览

```
用户请求
  ↓
FastAPI (REST + WebSocket)
  ↓
LangGraph StateGraph
  ├─ Router Node（意图分类）
  ├─ Entity Extractor（实体抽取 + 长期记忆补全）
  ├─ RAG Node（家电知识库检索）
  ├─ Tool Caller（设备控制 API）
  ├─ Scene Planner（多设备场景编排）
  └─ Responder（统一回复组装）
  ↓
Redis（短期记忆）+ Milvus（向量库 + 长期偏好）
  ↓
LangSmith Trace → RAGAS 评估 → Bad Case 沉淀
```

## 技术栈

| 层级 | 技术选型 |
|---|---|
| 智能体编排 | LangGraph >= 0.2.50 |
| LLM / Embedding | Qwen3-max / DashScope text-embedding-v4 |
| 向量库（Phase 1） | Chroma（本地持久化） |
| 向量库（Phase 2） | Milvus Standalone + BGE-Reranker |
| 短期记忆 | Redis 7 |
| Web 框架 | FastAPI + WebSocket |
| 评估 | LangSmith + RAGAS |

## 快速启动

### 1. 环境配置

```bash
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY 等配置
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动基础服务

```bash
docker compose up -d        # 启动 Redis
```

### 4. 加载知识库

```bash
python -c "from app.rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

### 5. 启动 API 服务（Phase 1 完成后）

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 启动调试 UI

```bash
streamlit run streamlit_debug/app.py
```

## 目录结构

```
Agent/
├── app/
│   ├── api/            # FastAPI 路由（REST + WebSocket）
│   ├── core/           # 配置（pydantic-settings）、异常
│   ├── models/         # Pydantic schemas + 评估日志模型
│   ├── agent/
│   │   ├── graph.py    # LangGraph 状态机拓扑
│   │   ├── state.py    # AgentState TypedDict
│   │   └── nodes/      # 各功能节点
│   ├── tools/          # 设备控制、天气、场景工具
│   ├── rag/            # 向量库封装 + 混合检索
│   ├── memory/         # Redis 短期 + 长期偏好图谱
│   └── evaluation/     # RAGAS 评估 + Bad Case 沉淀
├── data/               # 知识库文件 + 评估数据集
├── tests/              # 单元测试 + 端到端测试
├── streamlit_debug/    # 内部调试 UI
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 实施 Roadmap

- [x] **Phase 0**（当前）：工程基建，目录骨架，requirements，docker-compose
- [ ] **Phase 1**（第 1-2 周）：LangGraph 核心链路重构，FastAPI 接口，设备控制工具
- [ ] **Phase 2**（第 3-4 周）：Milvus 迁移，混合检索，Redis 分层记忆
- [ ] **Phase 3**（第 5-6 周）：LangSmith trace，RAGAS 自动评估，评估看板
- [ ] **Phase 4**（占位）：Bad Case → LoRA 微调数据集准备

## 原有客服功能保留说明

原扫地机器人客服功能（5 份 txt 知识库）作为**智能家居子设备**能力保留：
- `data/` 目录下所有知识库文件不变
- 由 `kb_query` 意图路由分支 + `rag_node` 处理
- 扫地机控制命令经 `device_control` 分支调用 `start_robot_vacuum()` 工具
