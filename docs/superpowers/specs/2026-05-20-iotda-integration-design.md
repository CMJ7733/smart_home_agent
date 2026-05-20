# IoTDA 接入设计文档

**日期:** 2026-05-20  
**状态:** 已审批，待实施  
**目标:** 将现有全 mock 的设备 API 替换为华为云 IoT 设备接入服务（IoTDA）真实云端往返，同时用 Python 模拟器替代真实硬件，实现"拟真"设备控制体验。

---

## 1. 背景与目标

项目当前的 `app/tools/device_api.py` 和 `app/tools/scene_api.py` 中所有设备控制函数均为 `raise NotImplementedError("Phase 1: 待实现")`，设备控制意图无法真正执行。

**接入 IoTDA 后的完整链路：**
Agent → IoTDA REST（同步命令）→ MQTT → 模拟器 → 属性上报 → IoTDA 设备影子

用户感受到的效果：对话指令触发真实的云端命令投递与设备状态更新，整条链路与生产智能家居系统一致，仅把物理硬件换成 Python 进程。

---

## 2. 方案选型

采用**方案 A：同步命令（Sync Command）**。

| 候选方案 | 结论 |
|---|---|
| A. 同步命令 | **采用** |
| B. 异步命令 + 轮询 | 复杂度高，不做 Phase 1 |
| C. 纯设备影子 PATCH | 无真实设备响应，不满足"拟真"目标 |

选择理由：模拟器始终在线，同步命令约束（设备必须在线、20s 内响应）等价于不存在；单次 HTTP 往返即可拿到完整结果；错误透明传播，便于调试。

---

## 3. 架构

```
┌────────────────────────────────────────────────────────────────┐
│  Agent 主进程 (FastAPI + LangGraph)                            │
│  ┌─────────────────┐   ┌──────────────────────────────────┐  │
│  │ tool_caller_node│──▶│ app/tools/iotda_client.py        │  │
│  │ scene_planner   │   │ (HTTP 同步命令 + 设备影子读取)   │  │
│  └─────────────────┘   └────────────┬─────────────────────┘  │
└────────────────────────────────────┬─┴─────────────────────────┘
                                     │ HTTPS (REST API)
                                     │ 鉴权: AK/SK → IAM Token (24h 缓存)
                                     ▼
                         ┌───────────────────────┐
                         │  华为云 IoTDA          │
                         │  - 4 个产品             │
                         │  - 7 个设备实例         │
                         │  - 设备影子 (真相源)    │
                         └─────┬─────────────────┘
                               │ MQTT (TLS 8883)
                               ▼
┌────────────────────────────────────────────────────────────────┐
│  独立进程: scripts/device_simulator.py                         │
│  ├── LightSimulator   × 2  (卧室-light、客厅-light)           │
│  ├── ACSimulator      × 2  (卧室-ac、客厅-ac)                 │
│  ├── CurtainSimulator × 2  (卧室-curtain、客厅-curtain)       │
│  └── VacuumSimulator  × 1  (全屋-vacuum)                      │
└────────────────────────────────────────────────────────────────┘
```

**关键设计决策：**
- `iotda_client.py` 封装所有 IoTDA REST 细节；上层 `@tool` 函数签名不变，`tool_caller_node` 无需修改。
- 设备影子是运行时唯一状态真相源；`query_device_status` 读影子而不读模拟器内存。
- 模拟器与 Agent 进程无直接通信，通过 IoTDA MQTT 解耦。
- 模拟器**不**加入 docker-compose，手动 `python scripts/device_simulator.py` 启动，避免凭证依赖导致 compose up 失败。

---

## 4. 组件

### 4.1 新增文件

| 文件 | 职责 |
|---|---|
| `app/tools/iotda_client.py` | IoTDA REST 封装：IAM Token 刷新、同步命令下发、设备影子读取 |
| `scripts/device_simulator.py` | 7 个模拟设备实例的 MQTT 连接、状态机、命令处理、属性上报 |
| `scripts/iotda_provision.py` | 一键建产品+设备；输出写入 `config/iotda_devices.yml` |
| `config/iotda_devices.yml` | 静态设备注册表：room+type → device_id + device_secret 映射（provision 后自动生成，供模拟器 MQTT 鉴权使用） |

### 4.2 修改文件

| 文件 | 变更 |
|---|---|
| `app/tools/device_api.py` | 5 个 `@tool` 函数 body 换为 `iotda_client.send_sync_command(...)` |
| `app/core/config.py` | 新增 `iotda_endpoint`、`iotda_project_id`、`iotda_ak`、`iotda_sk` |
| `.env.example` | 对应新增 4 个字段 |
| `requirements.txt` | 新增 `paho-mqtt` |

### 4.3 iotda_client.py 内部结构

```
IotdaAuth      — AK/SK 签名，缓存 IAM Token，到期前 5min 自动刷新
IotdaClient    — send_sync_command() / get_device_shadow()
DeviceRegistry — 读 config/iotda_devices.yml，room+type → device_id 查表
```

### 4.4 device_simulator.py 内部结构

```
DeviceSimulator   — 基类：MQTT 连接、主题订阅、消息路由、属性上报
LightSimulator    — on/off、color、brightness
ACSimulator       — power/temperature
CurtainSimulator  — position (open/close/stop)
VacuumSimulator   — working/idle/charging
```

### 4.5 不变文件

`app/agent/nodes/tool_caller.py`、`app/agent/nodes/scene_planner.py`、`app/agent/graph.py`、`app/agent/state.py`、所有 RAG / 记忆 / 评估模块。

---

## 5. IoTDA 产品与设备规划

### 5.1 产品（4 个）

| 产品名 | 设备类型 | 核心 Service | 核心 Command |
|---|---|---|---|
| SmartLight | 智能灯 | LightControl | SetLight(on, color, brightness) |
| SmartAC | 智能空调 | ACControl | SetTemperature(on, temperature) |
| SmartCurtain | 智能窗帘 | CurtainControl | SetCurtain(action: open/close/stop) |
| RobotVacuum | 扫地机器人 | VacuumControl | StartVacuum(room) |

### 5.2 设备实例（7 个）

| device_id（示意） | 产品 | 位置 |
|---|---|---|
| bedroom-light | SmartLight | 卧室 |
| livingroom-light | SmartLight | 客厅 |
| bedroom-ac | SmartAC | 卧室 |
| livingroom-ac | SmartAC | 客厅 |
| bedroom-curtain | SmartCurtain | 卧室 |
| livingroom-curtain | SmartCurtain | 客厅 |
| home-vacuum | RobotVacuum | 全屋 |

> 实际 device_id 由 IoTDA 生成，provision 后写入 `config/iotda_devices.yml`。

---

## 6. 数据流

### 6.1 设备命令链路

```
用户: "把卧室灯打开"
  → [router] intent: device_control
  → [entity_extractor] {device:"灯", room:"卧室", action:"开"}
  → [tool_caller_node] toggle_light(room="卧室", on=True)
      → DeviceRegistry.lookup("卧室","light") → device_id
      → IotdaClient.send_sync_command(device_id, "LightControl", "SetLight", {on:true,...})
          → POST /v5/iot/{project_id}/devices/{device_id}/sync-commands (HTTPS)
          → IoTDA → MQTT → LightSimulator
              → 更新内存 state
              → 上报属性 (properties/report)
              → 回 ACK (commands/{id}/response)
          → IoTDA 返回 HTTP 200 + result
      → "卧室灯已设置: on=True brightness=80 color=白色"
  → [responder] "好的，卧室的灯已经打开了。"
```

### 6.2 状态查询链路

```
query_device_status(device_id)
  → GET /v5/iot/{project_id}/devices/{device_id}/shadow
  → IoTDA 返回 {"reported": {...当前属性...}}
  → 格式化字符串返回 LLM
```

### 6.3 场景批量命令

`activate_scene("睡眠模式")` → 展开为 3 个动作 → **顺序**调用 3 次 `send_sync_command`（不并发，避免 IoTDA 频率限制）。

### 6.4 IAM Token 生命周期

- 首次调用时获取，缓存 token 和 `expire_at`
- 后续每次调用前检查：`expire_at - now < 5min` → 自动刷新
- Token 放入 `X-Auth-Token` Header

---

## 7. 错误处理

### 7.1 IoTDA REST 失败

| 场景 | 处理 |
|---|---|
| HTTP 4xx（凭证错误/设备不存在）| 抛 `IotdaError`，tool 层返回 `"设备调用失败: <错误信息>"` |
| HTTP 429 限速 | 按 `Retry-After` 等待后重试一次，二次失败直接报错 |
| HTTP 5xx / 网络超时（10s）| 抛异常，tool_caller_node catch 写入 tool_calls.result |
| IAM Token 刷新失败 | 抛 `IotdaAuthError`："IoTDA 鉴权失败，请检查 AK/SK" |

### 7.2 设备离线（模拟器未启动）

IoTDA 返回 `IOTDA.014011` → 映射为 `"设备离线 ({device_id})，请确认模拟器已启动"`。

### 7.3 模拟器 MQTT 断连

- `reconnect_on_failure=True`，指数退避自动重连
- 重连后重新订阅主题、上报当前内存 state
- 断连期间同步命令失败（语义正确）

### 7.4 设备注册表缺失

`DeviceRegistry.lookup()` 抛 `DeviceNotFoundError("请先运行 scripts/iotda_provision.py")`。这是启动前置条件，不在运行时处理。

---

## 8. 测试策略

### 8.1 单元测试（`tests/test_iotda_client.py`）

mock `requests.post/get`，覆盖：
- Token 缓存与自动刷新
- 429 重试逻辑
- 设备离线错误码映射
- `send_sync_command` payload 结构

本地无网络可运行。

### 8.2 集成测试（`tests/test_iotda_integration.py`）

标注 `@pytest.mark.integration`，默认跳过，需真实 IoTDA 凭证 + 模拟器在线：
- 向真实设备发同步命令，验证 result_code = 0
- 读设备影子，验证属性已更新

### 8.3 端到端冒烟测试（手动）

```bash
# 1. 启动模拟器
python scripts/device_simulator.py

# 2. 启动 FastAPI
uvicorn app.main:app --reload

# 3. 发送对话
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "把卧室灯打开"}'
```

验收标准：
1. 模拟器控制台打印 `[bedroom-light] SetLight: {on: True, ...}`
2. API 返回 `intent: device_control`，response 含"已打开"
3. IoTDA 控制台设备影子 `reported.on = true`

---

## 9. 实施前置条件

1. 华为云账号已开通 IoTDA（免费试用版），在控制台获得：
   - `IOTDA_ENDPOINT`（如 `xxxxxx.st1.iotda-device.cn-north-4.myhuaweicloud.com`）
   - `IOTDA_PROJECT_ID`
   - `IOTDA_AK` / `IOTDA_SK`（IAM 用户访问密钥，用于应用侧 REST 鉴权）
2. 将上述 4 个值填入 `.env`
3. 运行 `python scripts/iotda_provision.py`：自动创建 4 个产品、7 个设备，并把 `device_id` 和 `device_secret` 写入 `config/iotda_devices.yml`（模拟器 MQTT 鉴权使用）

---

## 10. 不在本次范围内

- 异步命令（可作后续扩展）
- Streamlit 实时设备状态面板（可单独 Phase）
- 真实硬件接入
- IoTDA 消息推送（AMQP/HTTPS 订阅）到 Agent 的反向通知
