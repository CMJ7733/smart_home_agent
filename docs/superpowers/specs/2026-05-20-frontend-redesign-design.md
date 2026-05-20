# 前端企业级改版设计文档

## 目标

将现有 205 行单文件 Streamlit 前端升级为企业级水准，同时服务两个场景：技术演示（视觉冲击力）和模拟真实智能家居产品（交互真实感）。

## 技术栈

- **框架**：Streamlit（保持不变）
- **新增依赖**：
  - `streamlit-option-menu` — 侧边栏导航
  - `plotly` — 评估看板图表（折线图 + 饼图）
- **主题**：现代浅色系（Linear / Vercel Dashboard 风格）
- **CSS**：通过 `st.markdown(unsafe_allow_html=True)` 注入全局自定义样式

## 色彩系统

| 用途 | 值 |
|------|-----|
| 页面背景 | `#F5F7FA` |
| 主色（按钮/高亮） | `#6366F1`（Indigo） |
| 强调色（在线/成功） | `#10B981`（绿） |
| 警告色（离线/错误） | `#EF4444`（红） |
| 卡片背景 | `#FFFFFF` |
| 卡片边框 | `#E2E8F0`，hover 左侧 3px `#6366F1` |
| 卡片阴影 | `0 4px 16px rgba(99,102,241,0.08)` |
| 主文字 | `#1E293B` |
| 次要文字 | `#64748B` |

字体：Inter（Google Fonts CDN）

## 文件结构

```
streamlit_app.py              ← 入口，只负责路由和侧边栏
app/ui/
├── styles.py                 ← 全局 CSS 字符串 + inject_css() 函数
├── components.py             ← 可复用组件：device_card、scene_card、status_badge、metric_card
└── pages/
    ├── chat.py               ← 对话页
    ├── devices.py            ← 设备中心页（新）
    ├── scenes.py             ← 场景控制页（新）
    ├── dashboard.py          ← 评估看板页
    └── eval_logs.py          ← Eval Logs 页
```

## 导航结构

侧边栏使用 `streamlit-option-menu`：

```
💬  对话
🏠  设备中心
🎬  场景控制
📊  评估看板
📝  Eval Logs
```

顶部 header bar（每页通用）：系统名称 + API 连通状态 + 在线设备数/总设备数。

---

## 页面设计

### 1. 对话页（`pages/chat.py`）

**布局：**
- 顶部：header bar（API ✅ / ❌，在线设备 N/7）
- 中部：消息气泡区（用户消息右对齐，助手消息左对齐），固定高度可滚动
- 底部：输入框 + 👍👎 反馈按钮（有 trace_id 时显示）

**设备操作展示：**
助手回复中的 tool_calls 改为**内联操作卡片**，不再使用 expander：
```
┌─────────────────────────────┐
│ 🏠 设备操作                  │
│ ✅ 卧室灯  → 已打开，亮度80%  │
│ ✅ 卧室空调 → 已设为 24°C    │
└─────────────────────────────┘
```
每条操作 `✅`（成功）或 `❌`（失败）前缀。

**数据来源：** 调用 `POST /api/v1/chat`，解析 response 和 tool_calls。

---

### 2. 设备中心页（`pages/devices.py`，新）

**布局：**
- 标题栏：设备中心 + 在线数量徽章 + 🔄 刷新按钮
- 按房间分组：卧室 / 客厅 / 全屋，每组横向排列设备卡片

**设备列表（共 7 台）：**
- 卧室：灯光、空调、窗帘
- 客厅：灯光、空调、窗帘
- 全屋：扫地机器人

**设备卡片规格：**
- 图标 + 设备名 + 状态
- 在线+开启：左侧 `#6366F1` 高亮条，绿色状态点
- 在线+关闭：灰色，无高亮
- 离线：红色边框 + "离线" 徽章

**数据来源：** 页面加载和刷新时批量调用 `IotdaClient.get_device_shadow()`（不轮询，手动刷新）。

---

### 3. 场景控制页（`pages/scenes.py`，新）

**布局：**
- 3 张场景卡片横排

**场景卡片规格（每张）：**
- 图标 + 场景名
- 涉及设备摘要（2-3 行文字）
- "一键激活" 按钮

**激活交互流程：**
1. 点击按钮 → spinner 出现
2. 逐步显示每台设备执行结果（`✅ 设备名 → 操作结果` 或 `❌ 失败原因`）
3. 全部完成后显示 "✅ 场景激活完成"

**场景列表（来自 `SCENE_TEMPLATES`）：**
- 🌙 睡眠模式：关卧室灯 · 空调26° · 关卧室窗帘
- 🚪 离家模式：关全屋灯 · 关全屋窗帘
- 🎬 观影模式：客厅暖光20% · 关客厅窗帘

**数据来源：** 直接调用 `activate_scene` tool，不经过 LLM。

---

### 4. 评估看板页（`pages/dashboard.py`）

**布局：**
- 顶部：时间范围滑块（1-30天）+ 刷新按钮
- 第一行：4 个 metric 卡片（总对话轮数 / Bad Cases / 👍 赞 / 👎 踩），带趋势副标题
- 第二行：Plotly 折线图（RAGAS 3 项指标趋势，按日期）
- 第三行：Plotly 饼图（意图分布：device_control / kb_query / chitchat / scene）

**数据来源：** 调用 `GET /api/v1/eval/dashboard?days=N`，折线图和饼图从返回数据本地计算。

---

### 5. Eval Logs 页（`pages/eval_logs.py`）

**布局：**
- 顶部工具栏：搜索框 + 意图筛选下拉（全部/device_control/kb_query/chitchat/scene）
- 主体：`st.dataframe` 表格展示（时间、查询摘要、意图、反馈、RAGAS 分）
- RAGAS 分 < 0.6 标红 ⚠️
- 表格下方提供行号选择器（`st.selectbox`），选中后展开该记录详情：完整对话 + 召回上下文 + tool_calls 轨迹

**数据来源：** 直接读取 `EvalLogRepo`（不经过 FastAPI）。

---

## 可复用组件（`components.py`）

| 函数 | 作用 |
|------|------|
| `inject_css()` | 注入全局样式（调用一次，放在 streamlit_app.py 顶部） |
| `header_bar(api_ok, online_count, total_count)` | 通用顶部状态栏 |
| `device_card(name, icon, status, properties)` | 设备状态卡片 |
| `scene_card(name, icon, summary, on_activate)` | 场景卡片 |
| `metric_card(label, value, subtitle)` | 指标卡片 |
| `tool_call_card(tool_calls)` | 对话中的设备操作结果卡片 |
| `status_badge(online)` | 在线/离线徽章 |

---

## 依赖变更

`requirements.txt` 新增：
```
streamlit-option-menu>=0.3.6
plotly>=5.0.0
```

---

## 不在此次范围内

- WebSocket 流式对话（`/chat/stream`）的前端对接
- 设备卡片上的快捷控制按钮（点击直接控制设备，不经对话）
- 自定义 Streamlit theme（`~/.streamlit/config.toml`）与本次 CSS 方案二选一，本次用 CSS 注入
