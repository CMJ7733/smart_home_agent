# Smart Home Agent 测试文档

完整的手动测试指南，包括各个阶段的测试用例和验证方法。

---

## 目录

1. [环境准备](#环境准备)
2. [Phase 1：基础对话 + 设备控制](#phase-1基础对话--设备控制)
3. [Phase 2：短期记忆](#phase-2短期记忆)
4. [Phase 3：RAGAS 评估 + 看板](#phase-3ragas-评估--看板)
5. [前端测试 (Streamlit)](#前端测试-streamlit)
6. [故障排查](#故障排查)

---

## 环境准备

### 必要服务启动

```powershell
# 1. 启动 Redis（短期记忆）
docker compose up -d redis

# 2. 启动 Milvus（向量库）
docker compose up -d milvus

# 3. 安装新增依赖
pip install langchain-openai ragas sqlalchemy apscheduler

# 4. 准备 .env 文件
Copy-Item .env.example .env
# 编辑 .env，根据需要选择 LLM_PROVIDER=ollama 或 api
```

### 启动服务

**终端 1：后端 API**
```powershell
uvicorn app.main:app --reload
# 服务运行在 http://localhost:8000
```

**终端 2：前端 (可选)**
```powershell
streamlit run streamlit_app.py
# 自动打开 http://localhost:8501
```

**终端 3：Ollama (如果用本地模型)**
```powershell
ollama serve
# 或通过 Ollama 客户端启动
```

### 健康检查

```powershell
curl http://localhost:8000/api/v1/health
# 预期: {"status":"ok"}
```

---

## Phase 1：基础对话 + 设备控制

### 测试 1.1：健康检查

**测试用例**：
```powershell
curl http://localhost:8000/api/v1/health
```

**预期结果**：
```json
{
  "status": "ok"
}
```

---

### 测试 1.2：Chitchat 意图（闲聊）

**测试用例**：
```powershell
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "你好，今天天气怎么样？",
  "session_id": "test-chitchat-001",
  "user_id": "user-001"
}
EOF
```

**预期结果**：
- `response` 字段包含自然语言回复
- `intent` 为 `"chitchat"`
- `trace_id` 返回唯一 UUID

**验证**：
```powershell
# 确认响应不是设备命令格式
# 确认 trace_id 存在
```

---

### 测试 1.3：Device Control 意图（灯光控制）

**测试用例**：
```powershell
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "请打开客厅的灯",
  "session_id": "test-device-001",
  "user_id": "user-001"
}
EOF
```

**预期结果**：
- `intent` 为 `"device_control"`
- `response` 包含执行结果（例如 "已打开客厅灯光" 或 "执行设备命令成功"）
- 不包含 "None" 字符串（Bug 1 修复验证）

**验证**：
```powershell
# 检查 response 中是否有设备操作结果
# 确认日志中显示 "toggle_light.invoke" 调用
```

---

### 测试 1.4：Device Control 意图（温度调节）

**测试用例**：
```powershell
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "把卧室温度设置为 26 度",
  "session_id": "test-device-002",
  "user_id": "user-001"
}
EOF
```

**预期结果**：
- `intent` 为 `"device_control"`
- `response` 包含温度设置确认

---

### 测试 1.5：Device Control 意图（窗帘控制）

**测试用例**：
```powershell
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "打开客厅的窗帘",
  "session_id": "test-device-003",
  "user_id": "user-001"
}
EOF
```

**预期结果**：
- `intent` 为 `"device_control"`
- `response` 包含窗帘操作确认

---

### 测试 1.6：Device Control 意图（扫地机器人）

**测试用例**：
```powershell
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "启动客厅的扫地机器人",
  "session_id": "test-device-004",
  "user_id": "user-001"
}
EOF
```

**预期结果**：
- `intent` 为 `"device_control"`
- `response` 包含扫地机器人启动确认

---

### 测试 1.7：KB Query 意图（知识库查询）

**前置条件**：
- 知识库已加载（运行过 `python -m app.rag.vector_store` 导入文档）

**测试用例**：
```powershell
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "扫地机器人怎么维护？",
  "session_id": "test-kb-001",
  "user_id": "user-001"
}
EOF
```

**预期结果**：
- `intent` 为 `"kb_query"`
- `response` 包含知识库中的维护信息
- 如果没有加载知识库，返回默认应答

---

## Phase 2：短期记忆

### 测试 2.1：单轮对话 Eval Log 写入

**测试用例**：
```powershell
# 发送第一条消息
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "你好",
  "session_id": "test-memory-001",
  "user_id": "user-001"
}
EOF

# 检查 SQLite 是否有记录
python -c "
from app.db.eval_log_repo import EvalLogRepo
import json
logs = EvalLogRepo().query_recent(1)
print(json.dumps(logs, ensure_ascii=False, indent=2))
"
```

**预期结果**：
- SQLite 表 `eval_logs` 中出现 1 条记录
- 字段 `trace_id`, `user_id`, `query`, `response`, `created_at` 正确填充

---

### 测试 2.2：历史消息加载（Chat History）

**测试用例**：
```powershell
# 第一轮对话
$trace1 = (curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "我叫张三",
  "session_id": "test-history-001",
  "user_id": "user-001"
}
EOF
) | ConvertFrom-Json | Select-Object -ExpandProperty trace_id

# 第二轮对话（同一 session_id）
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "我叫什么名字？",
  "session_id": "test-history-001",
  "user_id": "user-001"
}
EOF
```

**预期结果**：
- 第二轮回复应该引用"张三"（说明 chat_history 被正确加载）
- 不应该说"我不知道你的名字"（这表示历史消息没有加载）

**验证**：
```powershell
# 查看 Redis 中存储的历史
redis-cli get "chat:test-history-001"
# 应该返回 JSON 序列化的消息列表
```

---

### 测试 2.3：Redis 连接容错

**测试用例**：
```powershell
# 关闭 Redis
docker stop redis

# 尝试发送请求
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "你好",
  "session_id": "test-fallback-001",
  "user_id": "user-001"
}
EOF

# 重启 Redis
docker start redis
```

**预期结果**：
- 即使 Redis 离线，请求仍然成功（降级为空历史）
- 日志中出现 `logger.warning` 信息
- 响应正常返回

---

## Phase 3：RAGAS 评估 + 看板

### 测试 3.1：Eval Log 反馈 API

**前置条件**：
- 已有至少 1 条 eval log（见测试 2.1）

**测试用例**：
```powershell
# 获取最近的 trace_id
$trace_id = python -c "
from app.db.eval_log_repo import EvalLogRepo
logs = EvalLogRepo().query_recent(1)
if logs:
    print(logs[0]['trace_id'])
"

# 提交赞反馈
curl -X POST "http://localhost:8000/api/v1/feedback?trace_id=$trace_id&feedback=1"

# 验证反馈已保存
python -c "
from app.db.eval_log_repo import EvalLogRepo
logs = EvalLogRepo().query_recent(1)
print(f'User Feedback: {logs[0][\"user_feedback\"]}')
"
```

**预期结果**：
- 反馈 API 返回 `{"status":"ok"}`
- SQLite 中 `user_feedback` 字段更新为 `1`

**验证踩反馈**：
```powershell
curl -X POST "http://localhost:8000/api/v1/feedback?trace_id=$trace_id&feedback=-1"
# user_feedback 应该更新为 -1
```

---

### 测试 3.2：评估看板 API（无 RAGAS 数据）

**测试用例**：
```powershell
curl "http://localhost:8000/api/v1/eval/dashboard?days=7"
```

**预期结果**：
```json
{
  "total_turns": 3,           // 实际数量
  "days": 7,
  "daily_metrics": {},        // 空，因为还没跑 RAGAS
  "bad_case_count": 0,
  "feedback_stats": {
    "thumbs_up": 1,           // 之前赞过的数量
    "thumbs_down": 0
  }
}
```

---

### 测试 3.3：手动触发 RAGAS 评估（需要 Ollama 或 API）

**前置条件**：
- 至少有 1 条 `intent=kb_query` 的 eval log
- Ollama 正常运行（或 API 可访问）

**准备 kb_query 记录**：
```powershell
# 发送知识库查询
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "message": "扫地机器人如何清洁？",
  "session_id": "test-ragas-001",
  "user_id": "user-001"
}
EOF

# 等 1 秒确保 eval log 已写入
Start-Sleep -Seconds 1
```

**手动评估**：
```powershell
# 评估今天的数据
python -m app.evaluation.run_ragas_eval 2026-05-09

# 查看日志输出，应该显示类似：
# [RAGAS] 开始评估 2026-05-09 的 eval logs
# [RAGAS] 评估 1 条记录...
# [RAGAS] 完成: 1 条评估，0 条 bad case
```

**验证评估结果**：
```powershell
# 检查是否生成 bad case 文件
Test-Path data/bad_cases/2026-05-09.jsonl

# 查看评估指标是否已更新
python -c "
from app.db.eval_log_repo import EvalLogRepo
logs = EvalLogRepo().query_recent(1)
print(logs[0]['eval_metrics_json'])
"
```

**预期结果**：
- 如果有 bad case（任意指标 < 0.6），生成 `data/bad_cases/2026-05-09.jsonl`
- SQLite 中 `eval_metrics_json` 字段更新为评估分数

---

### 测试 3.4：看板 API（有 RAGAS 数据）

**前置条件**：
- 已运行过 RAGAS 评估（见测试 3.3）

**测试用例**：
```powershell
curl "http://localhost:8000/api/v1/eval/dashboard?days=7"
```

**预期结果**：
```json
{
  "total_turns": 4,
  "days": 7,
  "daily_metrics": {
    "2026-05-09": {
      "faithfulness": 0.850,
      "answer_relevancy": 0.920,
      "context_precision": 0.880
    }
  },
  "bad_case_count": 0,
  "feedback_stats": {
    "thumbs_up": 1,
    "thumbs_down": 0
  }
}
```

---

### 测试 3.5：Bad Case 提取 + SFT 格式转换

**前置条件**：
- 至少有 1 条 bad case 文件（见测试 3.3）

**测试用例**：
```powershell
# 转换 bad case 为 SFT 格式
python -m app.evaluation.log_parser 2026-05-09

# 查看输出
Get-Content data/finetune_dataset/train.jsonl | Select-Object -First 1 | ConvertFrom-Json | ConvertTo-Json
```

**预期结果**：
```json
{
  "instruction": "你是智能家居助手，请根据用户问题给出准确、有依据的回答。",
  "input": "扫地机器人如何清洁？",
  "output": "根据维护文档...",
  "trajectory": [...],
  "scores": {
    "faithfulness": 0.55,
    "answer_relevancy": 0.58,
    "context_precision": 0.65
  }
}
```

---

## 前端测试 (Streamlit)

### 启动 Streamlit

```powershell
streamlit run streamlit_app.py
# 浏览器自动打开 http://localhost:8501
```

---

### 测试 4.1：对话标签页 - 发送消息

**操作步骤**：
1. 在 "输入问题..." 输入框输入："请打开客厅的灯"
2. 按 Enter 或点击输入框右侧的提交按钮
3. 等待"思考中..."完成

**预期结果**：
- 用户消息和 AI 响应都显示在对话框中
- 显示 intent、trace_id 等详情

---

### 测试 4.2：对话标签页 - 反馈功能

**操作步骤**：
1. 完成一条对话（见测试 4.1）
2. 点击 "👍 赞" 按钮
3. 检查是否出现 "反馈已提交" 提示

**预期结果**：
- 反馈成功提交
- 看板中 "thumbs_up" 数字增加

---

### 测试 4.3：对话标签页 - 清空对话

**操作步骤**：
1. 发送几条消息
2. 点击 "🔄 清空" 按钮

**预期结果**：
- 对话历史清空（本地 Streamlit session 清空，SQLite 记录保留）

---

### 测试 4.4：评估看板标签页

**操作步骤**：
1. 点击 "📊 评估看板" 标签
2. 拖动滑块改变时间范围（7 天 → 30 天）

**预期结果**：
- 显示总对话数、Bad Cases 数、赞踩统计
- 显示日均评估指标表格（如果有 RAGAS 数据）

---

### 测试 4.5：Eval Logs 标签页

**操作步骤**：
1. 点击 "📝 Eval Logs" 标签
2. 点击任意一条记录的可展开区域

**预期结果**：
- 显示该条记录的完整信息（query、response、评估指标、反馈等）

---

## WebSocket 流式对话（可选）

### 测试 5.1：WebSocket 连接

**使用 Python 测试**：
```python
import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/chat/stream/test-ws-001"
    async with websockets.connect(uri) as websocket:
        # 发送消息
        await websocket.send(json.dumps({
            "message": "你好",
            "user_id": "user-001"
        }))
        
        # 接收响应
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Response: {data}")

asyncio.run(test_websocket())
```

**预期结果**：
- 连接成功
- 接收到 `type=final` 的响应 JSON

---

## 完整端到端测试场景

### 场景 1：完整智能家居交互

```powershell
# 1. 用户向 Agent 问好
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d '{"message":"你好，我是小王","session_id":"e2e-001","user_id":"user-001"}'

# 2. 用户要求打开灯
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d '{"message":"请打开客厅的灯","session_id":"e2e-001","user_id":"user-001"}'

# 3. 用户询问天气（需要知识库数据）
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d '{"message":"今天天气怎么样？","session_id":"e2e-001","user_id":"user-001"}'

# 4. 验证历史被正确加载
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d '{"message":"我是谁？","session_id":"e2e-001","user_id":"user-001"}'
# 预期：Agent 应该回答"你是小王"
```

### 场景 2：评估流水线

```powershell
# 1. 发送多条 kb_query
for ($i = 1; $i -le 3; $i++) {
  curl -X POST http://localhost:8000/api/v1/chat `
    -H "Content-Type: application/json" `
    -d "{\"message\":\"扫地机器人问题 $i\",\"session_id\":\"eval-$i\",\"user_id\":\"user-001\"}"
}

# 2. 等待 eval log 写入
Start-Sleep -Seconds 2

# 3. 手动运行 RAGAS
python -m app.evaluation.run_ragas_eval 2026-05-09

# 4. 检查看板
curl "http://localhost:8000/api/v1/eval/dashboard?days=1"

# 5. 提取 bad case
python -m app.evaluation.log_parser 2026-05-09

# 6. 验证 SFT 数据集生成
Get-Content data/finetune_dataset/train.jsonl | Measure-Object -Line
```

---

## 故障排查

### 问题 1：API 返回 500 错误

**诊断**：
```powershell
# 检查后端日志中的 Traceback
# 常见原因：
# 1. Ollama 离线 → 改用 API provider
# 2. Redis 离线 → 检查 docker ps
# 3. Milvus 离线 → 检查 docker ps
```

**解决**：
```powershell
# 确认所有依赖服务运行
docker ps | grep -E 'redis|milvus'

# 或切换到 API provider
# 编辑 .env: LLM_PROVIDER=api
```

---

### 问题 2：Chat history 没有加载

**诊断**：
```powershell
# 检查 Redis 中是否有数据
redis-cli get "chat:test-history-001"

# 检查 short_term.py load() 是否返回空列表
python -c "
from app.memory.short_term import ShortTermMemory
from app.core.config import get_settings
mem = ShortTermMemory(get_settings().redis_url, get_settings().redis_ttl)
print(mem.load('test-history-001'))
"
```

**解决**：
- 确认 Redis 正常运行
- 检查 `redis_url` 是否正确（`.env` 中）
- 查看是否有异常被捕获（memory_writer_node 中 try/except）

---

### 问题 3：RAGAS 评估失败

**诊断**：
```powershell
# 检查 eval log 是否存在
python -c "
from app.db.eval_log_repo import EvalLogRepo
logs = EvalLogRepo().query_by_date('2026-05-09')
print(f'Total logs: {len(logs)}')
print(f'KB Query logs: {len([l for l in logs if l[\"intent\"]==\"kb_query\"])}')
"

# 检查是否有依赖库缺失
python -m pip show ragas datasets
```

**解决**：
- 确保有 `intent=kb_query` 的 eval log（否则 RAGAS 跳过）
- 安装缺失的依赖：`pip install ragas datasets`
- 查看 `run_ragas_eval.py` 日志输出中的错误信息

---

### 问题 4：Streamlit 连接不上后端

**诊断**：
```powershell
# 检查后端是否运行
curl http://localhost:8000/api/v1/health

# 检查 Streamlit 配置中的 API_BASE
# streamlit_app.py L8: API_BASE = "http://localhost:8000/api/v1"
```

**解决**：
- 确保后端已启动（`uvicorn` 运行中）
- 如果改了端口，同时更新 Streamlit 中的 `API_BASE`

---

## 测试检查清单

使用此清单追踪测试进度：

- [ ] **健康检查** — `/health` 返回 ok
- [ ] **Chitchat** — 闲聊能正常回复
- [ ] **设备控制** — 灯光、温度、窗帘、扫地机都能控制
- [ ] **知识库查询** — kb_query 返回正确的文档
- [ ] **Eval log 写入** — SQLite 记录生成
- [ ] **Chat history** — 同一 session 历史加载
- [ ] **反馈 API** — 赞踩反馈保存
- [ ] **看板 API** — 统计数据正确显示
- [ ] **RAGAS 评估** — bad case 生成
- [ ] **SFT 转换** — finetune_dataset 生成
- [ ] **Streamlit 对话** — 前端交互正常
- [ ] **Streamlit 看板** — 指标展示正确
- [ ] **WebSocket** — 流式对话连接正常
- [ ] **Redis 容错** — 离线时不崩溃
- [ ] **Milvus 容错** — 离线时不崩溃

---

## 性能基准（参考）

运行一次完整流水线的预期时间：

| 操作 | 时间 | 说明 |
|---|---|---|
| 单轮 chitchat | 2-5 秒 | 取决于 LLM |
| 单轮 device_control | 1-2 秒 | 快速路径 |
| 单轮 kb_query | 3-8 秒 | 包含 RAG 检索 |
| RAGAS 评估 10 条 | 30-60 秒 | 取决于 LLM 和网络 |
| Streamlit 刷新 | <1 秒 | 本地查询 |

---

## 常用命令速查

```powershell
# 启动全套服务
docker compose up -d redis milvus
uvicorn app.main:app --reload

# 查看 eval logs
python -c "from app.db.eval_log_repo import EvalLogRepo; import json; print(json.dumps(EvalLogRepo().query_recent(7), ensure_ascii=False, indent=2))"

# 手动评估
python -m app.evaluation.run_ragas_eval 2026-05-09

# 生成 SFT 数据
python -m app.evaluation.log_parser 2026-05-09

# 连接 Redis
redis-cli

# 查看 Milvus 集合
python -c "from pymilvus import Collection; c = Collection('smart_home_agent'); print(c.num_entities)"

# 清空 eval logs
python -c "import os; os.remove('data/eval_logs.db') if os.path.exists('data/eval_logs.db') else None"
```

---

**最后更新**：2026-05-09
**作者**：Smart Home Agent 项目
