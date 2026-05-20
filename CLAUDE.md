# 智能家居 Agent — 项目导航

## 主要代码在 `app/` 目录

所有活跃实现均在 `app/` 下。根目录的 `rag/`、`agent/` 是旧版实现，已被 `app/` 取代，勿修改。

## 目录结构

```
app/
├── agent/
│   ├── graph.py          # LangGraph StateGraph 入口（compile 后即 graph 对象）
│   ├── state.py          # AgentState TypedDict
│   └── nodes/
│       ├── router.py         # 意图路由（关键词规则，Phase 2 改 LLM）
│       ├── entity_extractor.py  # 设备/房间/动作实体抽取
│       ├── tool_caller.py    # 调用设备工具 / 执行场景动作列表
│       ├── scene_planner.py  # 场景关键词匹配 → tool_calls 动作列表
│       ├── rag_node.py       # BM25 + Milvus 混合检索 + BGE-Reranker
│       ├── chat_node.py      # 闲聊回复
│       ├── responder.py      # 统一回复组装
│       └── memory_writer.py  # 异步写 Redis 短期记忆
├── tools/
│   ├── iotda_client.py   # Huawei IoTDA REST 客户端（IAM Token 认证）
│   ├── device_api.py     # LangChain tools：toggle_light / set_temperature / control_curtain / start_robot_vacuum / query_device_status
│   ├── scene_api.py      # activate_scene tool + SCENE_TEMPLATES 场景模板
│   └── device_registry.py  # room+type → device_id/secret（读 config/iotda_devices.yml）
├── rag/
│   ├── retriever.py      # HybridRetriever：BM25 top-20 + Milvus top-20 → BGE-Reranker → top-3
│   └── vector_store.py   # Milvus VectorStoreService（langchain_milvus）
├── memory/
│   ├── short_term.py     # Redis 会话记忆
│   └── memory_graph.py   # 长期用户偏好图谱（Phase 2）
├── api/
│   └── endpoints.py      # FastAPI 路由：POST /chat，WS /chat/stream/{session_id}，GET /health
├── core/
│   └── config.py         # pydantic-settings，统一从 .env 读取所有配置
└── models/
    └── schemas.py        # ChatRequest / ChatResponse Pydantic 模型
```

## 关键配置

- **所有密钥和端点**：`.env`（已在 .gitignore，勿提交）
- **IoTDA 设备注册表**：`config/iotda_devices.yml`（房间 → device_id / device_secret）
- **RAG / Milvus 参数**：`config/milvus.yml`（chunk_size、collection_name 等）

## 运行方式

```bash
# 1. 启动 Docker（Redis + Milvus）
docker compose up -d

# 2. 启动设备模拟器（另开终端）
python scripts/device_simulator.py

# 3. 启动 Streamlit 前端
streamlit run app.py

# 4. 或启动 FastAPI 后端（如有 main.py）
# uvicorn main:app --reload
```

## 测试

```bash
# 单元测试（无需模拟器）
pytest tests/test_iotda_client.py -v

# 端到端冒烟测试（需模拟器 + Docker + LLM API 有余额）
python tests/smoke_test_iotda_e2e.py
```

## IoTDA 关键知识

- 实例类型：华为云 IoTDA **专享版**，需 IAM Token 认证（AK/SK 直签返回 401）
- 应用侧 REST endpoint：`IOTDA_ENDPOINT`（`iotda-app.xxx`）
- 设备侧 MQTT endpoint：`IOTDA_DEVICE_ENDPOINT`（`iotda-device.xxx`）
- MQTT 命令 topic：`$oc/devices/{id}/sys/commands/request_id={cmd_id}`
- MQTT ACK topic：`$oc/devices/{id}/sys/commands/response/request_id={cmd_id}`

## 待办

- **Phase 1**：Router 升级为 LLM few-shot（当前关键词规则）
- **Phase 2**：memory_graph 长期偏好接入 entity_extractor；`/memory` REST 接口
- **Phase 3**：LangSmith tracing；评估 DB + 看板；用户反馈接口
