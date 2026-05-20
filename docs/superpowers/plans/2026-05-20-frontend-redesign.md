# Frontend Enterprise Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the 205-line single-file Streamlit frontend into an enterprise-grade multi-page app with a modern light theme, real-time device status, scene control, and evaluation dashboard.

**Architecture:** New `app/ui/` package contains styles, reusable components, and one file per page. `streamlit_app.py` becomes a thin router that injects global CSS and delegates to page modules via `streamlit-option-menu`.

**Tech Stack:** Streamlit ≥1.36, streamlit-option-menu ≥0.3.6, Plotly ≥6.5 (already in requirements), custom CSS injection, Huawei IoTDA `IotdaClient.get_device_shadow()` for live device state, `EvalLogRepo` (SQLite/SQLAlchemy) for eval data.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `requirements.txt` | Add `streamlit-option-menu>=0.3.6` |
| Create | `app/ui/__init__.py` | Package marker |
| Create | `app/ui/styles.py` | Full CSS string + `inject_css()` |
| Create | `app/ui/components.py` | `inject_css`, `header_bar`, `device_card`, `scene_card`, `metric_card`, `tool_call_card`, `status_badge` |
| Create | `app/ui/pages/__init__.py` | Package marker |
| Create | `app/ui/pages/chat.py` | Chat bubbles, tool_call_card, 👍👎 feedback |
| Create | `app/ui/pages/devices.py` | 7 device cards grouped by room, shadow data |
| Create | `app/ui/pages/scenes.py` | 3 scene cards with live activation |
| Create | `app/ui/pages/dashboard.py` | 4 metric cards + Plotly line & pie charts |
| Create | `app/ui/pages/eval_logs.py` | Searchable table + detail expand |
| Rewrite | `streamlit_app.py` | option-menu router, inject_css call |

---

### Task 1: Add dependency and create package skeleton

**Files:**
- Modify: `requirements.txt`
- Create: `app/ui/__init__.py`
- Create: `app/ui/pages/__init__.py`

- [ ] **Step 1: Add streamlit-option-menu to requirements**

Edit `requirements.txt` — add after the `streamlit` line:
```
streamlit-option-menu>=0.3.6
```

- [ ] **Step 2: Create package markers**

Create `app/ui/__init__.py` (empty):
```python
```

Create `app/ui/pages/__init__.py` (empty):
```python
```

- [ ] **Step 3: Verify install**

```bash
pip install streamlit-option-menu
python -c "from streamlit_option_menu import option_menu; print('ok')"
```
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt app/ui/__init__.py app/ui/pages/__init__.py
git commit -m "feat(ui): scaffold app/ui package, add streamlit-option-menu dep"
```

---

### Task 2: Global CSS and styles

**Files:**
- Create: `app/ui/styles.py`

- [ ] **Step 1: Write the failing import test**

```python
# tests/test_ui_styles.py
from app.ui.styles import CSS, inject_css

def test_css_contains_key_tokens():
    assert "#F5F7FA" in CSS          # page background
    assert "#6366F1" in CSS          # primary color
    assert "Inter" in CSS            # font

def test_inject_css_returns_none(monkeypatch):
    import streamlit as st
    monkeypatch.setattr(st, "markdown", lambda *a, **kw: None)
    assert inject_css() is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_ui_styles.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'app.ui.styles'`

- [ ] **Step 3: Write `app/ui/styles.py`**

```python
import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Page background ── */
.stApp {
    background-color: #F5F7FA;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}

/* ── Cards ── */
.sh-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
    box-shadow: 0 4px 16px rgba(99,102,241,0.08);
    transition: border-left 0.15s;
}
.sh-card:hover {
    border-left: 3px solid #6366F1;
}
.sh-card-active {
    border-left: 3px solid #6366F1;
}

/* ── Header bar ── */
.sh-header {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 12px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.sh-header-title {
    font-size: 18px;
    font-weight: 600;
    color: #1E293B;
    flex: 1;
}

/* ── Status badges ── */
.sh-badge-online {
    background: #D1FAE5;
    color: #065F46;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 500;
}
.sh-badge-offline {
    background: #FEE2E2;
    color: #991B1B;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 500;
}

/* ── Chat bubbles ── */
.sh-bubble-user {
    background: #6366F1;
    color: #FFFFFF;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 16px;
    margin: 6px 0;
    max-width: 75%;
    margin-left: auto;
    word-wrap: break-word;
}
.sh-bubble-assistant {
    background: #FFFFFF;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 16px;
    margin: 6px 0;
    max-width: 75%;
    box-shadow: 0 2px 8px rgba(99,102,241,0.06);
    word-wrap: break-word;
}

/* ── Tool call card ── */
.sh-tool-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 8px;
    font-size: 13px;
}
.sh-tool-card-title {
    font-weight: 600;
    color: #475569;
    margin-bottom: 6px;
}
.sh-tool-result-ok  { color: #065F46; }
.sh-tool-result-err { color: #991B1B; }

/* ── Metric card ── */
.sh-metric {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 16px rgba(99,102,241,0.06);
}
.sh-metric-value {
    font-size: 36px;
    font-weight: 700;
    color: #1E293B;
}
.sh-metric-label {
    font-size: 13px;
    color: #64748B;
    margin-top: 4px;
}
.sh-metric-sub {
    font-size: 12px;
    color: #94A3B8;
    margin-top: 2px;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background-color: #6366F1;
    border-color: #6366F1;
}
.stButton > button[kind="primary"]:hover {
    background-color: #4F46E5;
}
"""


def inject_css() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_ui_styles.py -v
```
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/ui/styles.py tests/test_ui_styles.py
git commit -m "feat(ui): global CSS with Inter font, card/bubble/metric styles"
```

---

### Task 3: Reusable UI components

**Files:**
- Create: `app/ui/components.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_components.py
import pytest

def test_imports():
    from app.ui.components import (
        header_bar, device_card, scene_card,
        metric_card, tool_call_card, status_badge,
    )

def test_status_badge_returns_html():
    from app.ui.components import status_badge
    online_html = status_badge(True)
    offline_html = status_badge(False)
    assert "在线" in online_html
    assert "离线" in offline_html
    assert "sh-badge-online" in online_html
    assert "sh-badge-offline" in offline_html
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_ui_components.py -v
```
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `app/ui/components.py`**

```python
import streamlit as st


def status_badge(online: bool) -> str:
    if online:
        return '<span class="sh-badge-online">● 在线</span>'
    return '<span class="sh-badge-offline">● 离线</span>'


def header_bar(api_ok: bool, online_count: int, total_count: int) -> None:
    api_indicator = "✅ API 已连接" if api_ok else "❌ API 离线"
    st.markdown(
        f"""<div class="sh-header">
            <span class="sh-header-title">🏠 Smart Home Agent</span>
            <span style="color:#64748B;font-size:13px;">{api_indicator}</span>
            <span style="color:#64748B;font-size:13px;">
                设备在线 {online_count}/{total_count}
            </span>
        </div>""",
        unsafe_allow_html=True,
    )


def device_card(name: str, icon: str, online: bool, on: bool, properties: dict) -> None:
    active_class = "sh-card-active" if (online and on) else ""
    border_color = "#EF4444" if not online else "#E2E8F0"
    prop_lines = "".join(
        f'<div style="font-size:12px;color:#64748B;">{k}: {v}</div>'
        for k, v in properties.items()
    )
    badge = status_badge(online)
    st.markdown(
        f"""<div class="sh-card {active_class}"
                 style="border-color:{border_color};">
            <div style="font-size:24px;margin-bottom:8px;">{icon}</div>
            <div style="font-weight:600;color:#1E293B;margin-bottom:4px;">{name}</div>
            {badge}
            <div style="margin-top:8px;">{prop_lines}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def scene_card(name: str, icon: str, summary: str) -> None:
    st.markdown(
        f"""<div class="sh-card">
            <div style="font-size:28px;margin-bottom:8px;">{icon}</div>
            <div style="font-weight:600;color:#1E293B;font-size:16px;margin-bottom:8px;">
                {name}
            </div>
            <div style="font-size:13px;color:#64748B;line-height:1.6;margin-bottom:12px;">
                {summary}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str | int, subtitle: str = "") -> None:
    sub_html = (
        f'<div class="sh-metric-sub">{subtitle}</div>' if subtitle else ""
    )
    st.markdown(
        f"""<div class="sh-metric">
            <div class="sh-metric-value">{value}</div>
            <div class="sh-metric-label">{label}</div>
            {sub_html}
        </div>""",
        unsafe_allow_html=True,
    )


def tool_call_card(tool_calls: list[dict]) -> None:
    if not tool_calls:
        return
    rows = ""
    for tc in tool_calls:
        ok = tc.get("success", True)
        icon = "✅" if ok else "❌"
        css_cls = "sh-tool-result-ok" if ok else "sh-tool-result-err"
        device = tc.get("device", tc.get("action", ""))
        result = tc.get("result", "")
        rows += (
            f'<div class="{css_cls}">'
            f"{icon} {device} → {result}"
            f"</div>"
        )
    st.markdown(
        f"""<div class="sh-tool-card">
            <div class="sh-tool-card-title">🏠 设备操作</div>
            {rows}
        </div>""",
        unsafe_allow_html=True,
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_ui_components.py -v
```
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/ui/components.py tests/test_ui_components.py
git commit -m "feat(ui): reusable components — header_bar, device_card, scene_card, metric_card, tool_call_card, status_badge"
```

---

### Task 4: Chat page

**Files:**
- Create: `app/ui/pages/chat.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_pages_chat.py
def test_chat_module_importable():
    import app.ui.pages.chat  # noqa: F401

def test_render_function_exists():
    from app.ui.pages.chat import render
    import inspect
    assert callable(render)
    assert len(inspect.signature(render).parameters) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_ui_pages_chat.py -v
```
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `app/ui/pages/chat.py`**

```python
import uuid
import requests
import streamlit as st
from app.ui.components import header_bar, tool_call_card

API_BASE = "http://localhost:8000/api/v1"


def _check_api() -> tuple[bool, int, int]:
    """Returns (api_ok, online_count, total_count). Never raises."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=3)
        api_ok = resp.status_code == 200
    except Exception:
        api_ok = False
    return api_ok, 0, 7


def render() -> None:
    # ── session state init ──
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "user_id" not in st.session_state:
        st.session_state.user_id = "user-001"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_trace_id" not in st.session_state:
        st.session_state.last_trace_id = ""

    api_ok, online, total = _check_api()
    header_bar(api_ok, online, total)

    # ── chat area ──
    chat_container = st.container(height=460, border=False)
    with chat_container:
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                st.markdown(
                    f'<div style="display:flex;justify-content:flex-end;">'
                    f'<div class="sh-bubble-user">{content}</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="sh-bubble-assistant">{content}</div>',
                    unsafe_allow_html=True,
                )
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    tool_call_card(tool_calls)

    # ── input bar ──
    user_input = st.chat_input("输入指令，例如：把卧室灯打开，亮度80%")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("处理中…"):
            try:
                resp = requests.post(
                    f"{API_BASE}/chat",
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id,
                        "user_id": st.session_state.user_id,
                    },
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data.get("response") or "（后端返回了空字符串）"
                st.session_state.last_trace_id = data.get("trace_id", "")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": data.get("tool_calls", []),
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"⚠️ 请求失败: {e}",
                })
        st.rerun()

    # ── feedback ──
    if st.session_state.last_trace_id:
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 6])
        with col1:
            if st.button("👍", use_container_width=True, key="fb_up"):
                requests.post(
                    f"{API_BASE}/feedback",
                    params={"trace_id": st.session_state.last_trace_id, "feedback": 1},
                    timeout=5,
                )
                st.toast("感谢反馈 👍")
        with col2:
            if st.button("👎", use_container_width=True, key="fb_down"):
                requests.post(
                    f"{API_BASE}/feedback",
                    params={"trace_id": st.session_state.last_trace_id, "feedback": -1},
                    timeout=5,
                )
                st.toast("感谢反馈 👎")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_ui_pages_chat.py -v
```
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/ui/pages/chat.py tests/test_ui_pages_chat.py
git commit -m "feat(ui): chat page with bubble layout and inline tool-call card"
```

---

### Task 5: Device center page

**Files:**
- Create: `app/ui/pages/devices.py`

Context: `DeviceRegistry.all_devices()` returns `[{"room":…,"type":…,"device_id":…,"device_secret":…}, …]` for all 7 devices (卧室: light/curtain/ac, 客厅: light/curtain/ac, 全屋: vacuum). `IotdaClient.get_device_shadow(device_id)` returns the IoTDA shadow dict; relevant properties live at `shadow[0]["reported"]["properties"]`. Device status (online/offline) is at shadow root key `device_status == "ONLINE"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_pages_devices.py
def test_devices_module_importable():
    import app.ui.pages.devices  # noqa: F401

def test_render_exists():
    from app.ui.pages.devices import render
    import inspect
    assert callable(render)
    assert len(inspect.signature(render).parameters) == 0

def test_device_type_to_icon_covers_known_types():
    from app.ui.pages.devices import DEVICE_ICONS
    for t in ("light", "ac", "curtain", "vacuum"):
        assert t in DEVICE_ICONS
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_ui_pages_devices.py -v
```
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `app/ui/pages/devices.py`**

```python
import streamlit as st
from app.ui.components import header_bar, device_card, status_badge
from app.tools.device_registry import DeviceRegistry
from app.tools.iotda_client import IotdaClient
from app.core.config import get_settings

DEVICE_ICONS = {
    "light":   "💡",
    "ac":      "❄️",
    "curtain": "🪟",
    "vacuum":  "🤖",
}

DEVICE_NAMES = {
    "light":   "灯光",
    "ac":      "空调",
    "curtain": "窗帘",
    "vacuum":  "扫地机器人",
}

ROOM_ORDER = ["卧室", "客厅", "全屋"]


def _load_shadows(devices: list[dict]) -> dict[str, dict]:
    """Returns {device_id: shadow_properties_dict}. Never raises."""
    s = get_settings()
    client = IotdaClient(s.iotda_endpoint, s.iotda_project_id, s.iotda_ak, s.iotda_sk)
    result = {}
    for dev in devices:
        try:
            shadow = client.get_device_shadow(dev["device_id"])
            items = shadow.get("shadow", [])
            props = items[0].get("reported", {}).get("properties", {}) if items else {}
            status = shadow.get("device_status", "OFFLINE")
            result[dev["device_id"]] = {"online": status == "ONLINE", **props}
        except Exception:
            result[dev["device_id"]] = {"online": False}
    return result


def render() -> None:
    registry = DeviceRegistry()
    all_devs = registry.all_devices()

    if "device_shadows" not in st.session_state:
        st.session_state.device_shadows = {}

    col_title, col_btn = st.columns([5, 1])
    with col_title:
        online_count = sum(
            1 for d in all_devs
            if st.session_state.device_shadows.get(d["device_id"], {}).get("online", False)
        )
        st.markdown(
            f"## 设备中心 "
            f'<span class="sh-badge-online">{online_count} 在线</span>',
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("🔄 刷新", use_container_width=True):
            st.session_state.device_shadows = _load_shadows(all_devs)
            st.rerun()

    if not st.session_state.device_shadows:
        st.info("点击「刷新」加载设备状态")
        return

    # Group devices by room
    rooms: dict[str, list[dict]] = {}
    for dev in all_devs:
        rooms.setdefault(dev["room"], []).append(dev)

    for room in ROOM_ORDER:
        if room not in rooms:
            continue
        st.markdown(f"### {room}")
        cols = st.columns(len(rooms[room]))
        for col, dev in zip(cols, rooms[room]):
            with col:
                shadow = st.session_state.device_shadows.get(dev["device_id"], {})
                online = shadow.get("online", False)
                on = shadow.get("on", False) if dev["type"] != "vacuum" else False
                display_props = {k: v for k, v in shadow.items() if k not in ("online", "on")}
                device_card(
                    name=f"{room}{DEVICE_NAMES.get(dev['type'], dev['type'])}",
                    icon=DEVICE_ICONS.get(dev["type"], "📱"),
                    online=online,
                    on=on,
                    properties=display_props,
                )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_ui_pages_devices.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/ui/pages/devices.py tests/test_ui_pages_devices.py
git commit -m "feat(ui): device center page with room grouping and IoTDA shadow state"
```

---

### Task 6: Scene control page

**Files:**
- Create: `app/ui/pages/scenes.py`

Context: `activate_scene` is a LangChain `@tool`. Call it via `activate_scene.invoke({"scene_name": name})` — it returns a Chinese string like `"睡眠模式已激活：…"`. Scene templates (from `app/tools/scene_api.py`): 睡眠模式 (🌙), 离家模式 (🚪), 观影模式 (🎬).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_pages_scenes.py
def test_scenes_module_importable():
    import app.ui.pages.scenes  # noqa: F401

def test_render_exists():
    from app.ui.pages.scenes import render, SCENES
    import inspect
    assert callable(render)
    assert len(SCENES) == 3
    scene_names = [s["name"] for s in SCENES]
    assert "睡眠模式" in scene_names
    assert "离家模式" in scene_names
    assert "观影模式" in scene_names
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_ui_pages_scenes.py -v
```
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `app/ui/pages/scenes.py`**

```python
import streamlit as st
from app.ui.components import scene_card

SCENES = [
    {
        "name": "睡眠模式",
        "icon": "🌙",
        "summary": "关卧室灯 · 空调调至 26°C · 关卧室窗帘",
    },
    {
        "name": "离家模式",
        "icon": "🚪",
        "summary": "关全屋灯 · 关全屋窗帘",
    },
    {
        "name": "观影模式",
        "icon": "🎬",
        "summary": "客厅暖光 20% · 关客厅窗帘",
    },
]


def render() -> None:
    st.markdown("## 场景控制")
    st.markdown(
        '<p style="color:#64748B;font-size:14px;margin-bottom:20px;">'
        "一键激活预设场景，所有设备同步执行</p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(SCENES))
    for col, scene in zip(cols, SCENES):
        with col:
            scene_card(scene["name"], scene["icon"], scene["summary"])
            if st.button(
                "一键激活",
                key=f"activate_{scene['name']}",
                use_container_width=True,
                type="primary",
            ):
                _run_scene(scene["name"])


def _run_scene(scene_name: str) -> None:
    from app.tools.scene_api import activate_scene, SCENE_TEMPLATES

    actions = SCENE_TEMPLATES.get(scene_name, [])
    status_placeholder = st.empty()

    step_results: list[str] = []
    with st.spinner(f"正在激活「{scene_name}」…"):
        from app.tools.device_api import toggle_light, set_temperature, control_curtain, start_robot_vacuum
        tool_map = {
            "toggle_light": toggle_light,
            "set_temperature": set_temperature,
            "control_curtain": control_curtain,
            "start_robot_vacuum": start_robot_vacuum,
        }
        for action in actions:
            fn = tool_map.get(action.get("tool", ""))
            if not fn:
                step_results.append(f"❌ 未知工具: {action.get('tool')}")
                continue
            try:
                result = fn.invoke(action.get("args", {}))
                step_results.append(f"✅ {result}")
            except Exception as e:
                step_results.append(f"❌ 失败: {e}")
            status_placeholder.markdown("\n\n".join(step_results))

    status_placeholder.success(f"✅ 场景「{scene_name}」激活完成")
    for line in step_results:
        st.markdown(f"- {line}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_ui_pages_scenes.py -v
```
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/ui/pages/scenes.py tests/test_ui_pages_scenes.py
git commit -m "feat(ui): scene control page with step-by-step activation feedback"
```

---

### Task 7: Evaluation dashboard page

**Files:**
- Create: `app/ui/pages/dashboard.py`

Context: `GET /api/v1/eval/dashboard?days=N` returns:
```json
{
  "total_turns": 42,
  "days": 7,
  "daily_metrics": {"2026-05-15": {"faithfulness": 0.9, "answer_relevancy": 0.85, "context_precision": 0.8}},
  "bad_case_count": 3,
  "feedback_stats": {"thumbs_up": 10, "thumbs_down": 2}
}
```
Intent distribution must be computed from `EvalLogRepo().query_recent(days)` locally (the API does not return it). Plotly chart colors: primary `#6366F1`, secondary `#10B981`, tertiary `#F59E0B`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_pages_dashboard.py
def test_dashboard_module_importable():
    import app.ui.pages.dashboard  # noqa: F401

def test_render_exists():
    from app.ui.pages.dashboard import render
    import inspect
    assert callable(render)

def test_build_intent_dist_returns_dict():
    from app.ui.pages.dashboard import _build_intent_dist
    logs = [
        {"intent": "device_control"},
        {"intent": "device_control"},
        {"intent": "kb_query"},
        {"intent": "chitchat"},
    ]
    result = _build_intent_dist(logs)
    assert result["device_control"] == 2
    assert result["kb_query"] == 1
    assert result["chitchat"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_ui_pages_dashboard.py -v
```
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `app/ui/pages/dashboard.py`**

```python
import requests
import streamlit as st
import plotly.graph_objects as go
from collections import Counter
from app.ui.components import metric_card

API_BASE = "http://localhost:8000/api/v1"

RAGAS_COLORS = ["#6366F1", "#10B981", "#F59E0B"]
INTENT_COLORS = ["#6366F1", "#10B981", "#F59E0B", "#EF4444"]


def _build_intent_dist(logs: list[dict]) -> dict[str, int]:
    return dict(Counter(l["intent"] for l in logs if l.get("intent")))


def render() -> None:
    st.markdown("## 评估看板")

    col_slider, col_btn = st.columns([4, 1])
    with col_slider:
        days = st.slider("时间范围（天）", 1, 30, 7, key="dash_days")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 刷新", key="dash_refresh")

    try:
        resp = requests.get(f"{API_BASE}/eval/dashboard", params={"days": days}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        st.error(f"获取看板数据失败: {e}")
        return

    total = data.get("total_turns", 0)
    bad = data.get("bad_case_count", 0)
    up = data.get("feedback_stats", {}).get("thumbs_up", 0)
    down = data.get("feedback_stats", {}).get("thumbs_down", 0)

    # ── Row 1: metric cards ──
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("总对话轮数", total, f"最近 {days} 天")
    with m2:
        metric_card("Bad Cases", bad)
    with m3:
        metric_card("👍 赞", up)
    with m4:
        metric_card("👎 踩", down)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: RAGAS line chart ──
    daily = data.get("daily_metrics", {})
    if daily:
        dates = sorted(daily.keys())
        metric_keys = ["faithfulness", "answer_relevancy", "context_precision"]
        metric_labels = ["Faithfulness", "Answer Relevancy", "Context Precision"]

        fig = go.Figure()
        for key, label, color in zip(metric_keys, metric_labels, RAGAS_COLORS):
            values = [daily[d].get(key, 0) for d in dates]
            fig.add_trace(go.Scatter(
                x=dates, y=values, name=label,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=6),
            ))

        fig.update_layout(
            title="RAGAS 指标趋势",
            yaxis=dict(range=[0, 1]),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(family="Inter", color="#1E293B"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无 RAGAS 评估数据")

    # ── Row 3: intent pie ──
    try:
        from app.db.eval_log_repo import EvalLogRepo
        logs = EvalLogRepo().query_recent(days)
        intent_dist = _build_intent_dist(logs)
    except Exception:
        intent_dist = {}

    if intent_dist:
        pie = go.Figure(go.Pie(
            labels=list(intent_dist.keys()),
            values=list(intent_dist.values()),
            marker=dict(colors=INTENT_COLORS),
            hole=0.4,
            textinfo="label+percent",
        ))
        pie.update_layout(
            title="意图分布",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(family="Inter", color="#1E293B"),
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(pie, use_container_width=True)
    else:
        st.info("暂无意图分布数据")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_ui_pages_dashboard.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/ui/pages/dashboard.py tests/test_ui_pages_dashboard.py
git commit -m "feat(ui): evaluation dashboard with Plotly RAGAS line chart and intent pie"
```

---

### Task 8: Eval Logs page

**Files:**
- Create: `app/ui/pages/eval_logs.py`

Context: `EvalLogRepo().query_recent(days)` returns list of dicts with keys: `trace_id`, `user_id`, `query`, `intent`, `response`, `contexts_json` (JSON string), `trajectory_json` (JSON string), `user_feedback` (1/-1/None), `eval_metrics_json` (JSON string or None), `created_at` (datetime str). RAGAS score for display: average of values in `eval_metrics_json` dict (skip if absent). A score < 0.6 should be flagged with ⚠️.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_pages_eval_logs.py
def test_eval_logs_module_importable():
    import app.ui.pages.eval_logs  # noqa: F401

def test_render_exists():
    from app.ui.pages.eval_logs import render
    import inspect
    assert callable(render)

def test_avg_score():
    from app.ui.pages.eval_logs import _avg_score
    assert _avg_score('{"faithfulness": 0.8, "answer_relevancy": 0.6}') == pytest.approx(0.7)
    assert _avg_score(None) is None
    assert _avg_score("") is None

def test_feedback_label():
    from app.ui.pages.eval_logs import _feedback_label
    assert _feedback_label(1) == "👍"
    assert _feedback_label(-1) == "👎"
    assert _feedback_label(None) == "-"
```

Note: add `import pytest` at the top of the test file.

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_ui_pages_eval_logs.py -v
```
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `app/ui/pages/eval_logs.py`**

```python
import json
import streamlit as st

INTENT_OPTIONS = ["全部", "device_control", "kb_query", "chitchat", "scene"]


def _avg_score(metrics_json: str | None) -> float | None:
    if not metrics_json:
        return None
    try:
        d = json.loads(metrics_json)
        vals = [v for v in d.values() if isinstance(v, (int, float))]
        return sum(vals) / len(vals) if vals else None
    except Exception:
        return None


def _feedback_label(val: int | None) -> str:
    if val == 1:
        return "👍"
    if val == -1:
        return "👎"
    return "-"


def render() -> None:
    st.markdown("## Eval Logs")

    col_search, col_intent = st.columns([3, 1])
    with col_search:
        search = st.text_input("搜索查询内容", placeholder="关键词…", key="log_search")
    with col_intent:
        intent_filter = st.selectbox("意图筛选", INTENT_OPTIONS, key="log_intent")

    try:
        from app.db.eval_log_repo import EvalLogRepo
        logs = EvalLogRepo().query_recent(30)
    except Exception as e:
        st.error(f"加载 Eval Logs 失败: {e}")
        return

    if search:
        logs = [l for l in logs if search.lower() in l["query"].lower()]
    if intent_filter != "全部":
        logs = [l for l in logs if l["intent"] == intent_filter]

    logs = list(reversed(logs))

    if not logs:
        st.info("暂无符合条件的记录")
        return

    # Build display table
    rows = []
    for i, log in enumerate(logs):
        score = _avg_score(log.get("eval_metrics_json"))
        score_str = f"⚠️ {score:.2f}" if (score is not None and score < 0.6) else (f"{score:.2f}" if score else "-")
        rows.append({
            "#": i,
            "时间": log["created_at"][:16] if log.get("created_at") else "-",
            "查询摘要": log["query"][:60],
            "意图": log.get("intent", "-"),
            "反馈": _feedback_label(log.get("user_feedback")),
            "RAGAS 分": score_str,
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Detail view
    idx = st.selectbox(
        "选择行号查看详情",
        options=range(len(logs)),
        format_func=lambda i: f"#{i} — {logs[i]['query'][:50]}",
        key="log_detail_idx",
    )

    if idx is not None:
        log = logs[idx]
        st.divider()
        st.markdown(f"**Trace ID:** `{log.get('trace_id', '-')}`")
        st.markdown(f"**用户:** {log.get('user_id', '-')}  |  **意图:** {log.get('intent', '-')}")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**完整查询**")
            st.write(log.get("query", "-"))
            st.markdown("**回复**")
            st.write(log.get("response", "-"))
        with c2:
            st.markdown("**召回上下文**")
            try:
                contexts = json.loads(log.get("contexts_json", "[]"))
                for ctx in contexts:
                    st.markdown(f"- {ctx[:120]}")
            except Exception:
                st.write("-")

            st.markdown("**Tool Calls 轨迹**")
            try:
                traj = json.loads(log.get("trajectory_json", "[]"))
                for t in traj:
                    st.json(t)
            except Exception:
                st.write("-")

        if log.get("eval_metrics_json"):
            st.markdown("**RAGAS 指标**")
            try:
                st.json(json.loads(log["eval_metrics_json"]))
            except Exception:
                pass
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_ui_pages_eval_logs.py -v
```
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add app/ui/pages/eval_logs.py tests/test_ui_pages_eval_logs.py
git commit -m "feat(ui): eval logs page with search, intent filter, and detail expand"
```

---

### Task 9: Rewrite `streamlit_app.py` as the routing entry point

**Files:**
- Rewrite: `streamlit_app.py`

Context: `streamlit-option-menu` usage:
```python
from streamlit_option_menu import option_menu
selected = option_menu(
    menu_title=None,
    options=["对话", "设备中心", "场景控制", "评估看板", "Eval Logs"],
    icons=["chat-dots", "house", "film", "bar-chart", "journal-text"],
    default_index=0,
    orientation="vertical",
)
```
Place the `option_menu` inside `st.sidebar`. The `st.set_page_config` call must remain first.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_streamlit_app.py
def test_page_modules_all_importable():
    from app.ui.pages import chat, devices, scenes, dashboard, eval_logs

def test_inject_css_importable():
    from app.ui.styles import inject_css
```

- [ ] **Step 2: Run test to verify it passes (all imports should exist now)**

```bash
pytest tests/test_streamlit_app.py -v
```
Expected: PASS (since Tasks 2-8 are done)

- [ ] **Step 3: Rewrite `streamlit_app.py`**

```python
import streamlit as st

st.set_page_config(
    page_title="Smart Home Agent",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.ui.styles import inject_css
from app.ui.pages import chat, devices, scenes, dashboard, eval_logs
from streamlit_option_menu import option_menu

inject_css()

with st.sidebar:
    st.markdown(
        '<div style="font-weight:700;font-size:18px;color:#1E293B;padding:12px 0 20px;">'
        "🏠 Smart Home</div>",
        unsafe_allow_html=True,
    )
    selected = option_menu(
        menu_title=None,
        options=["对话", "设备中心", "场景控制", "评估看板", "Eval Logs"],
        icons=["chat-dots", "house", "film", "bar-chart", "journal-text"],
        default_index=0,
        styles={
            "container": {"padding": "0", "background-color": "#FFFFFF"},
            "icon": {"color": "#6366F1", "font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "color": "#475569",
                "border-radius": "8px",
                "margin": "2px 0",
            },
            "nav-link-selected": {
                "background-color": "#EEF2FF",
                "color": "#6366F1",
                "font-weight": "600",
            },
        },
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("Smart Home Agent v1.0")

PAGE_MAP = {
    "对话": chat.render,
    "设备中心": devices.render,
    "场景控制": scenes.render,
    "评估看板": dashboard.render,
    "Eval Logs": eval_logs.render,
}

PAGE_MAP[selected]()
```

- [ ] **Step 4: Smoke-check the app starts**

```bash
streamlit run streamlit_app.py --server.headless true &
sleep 4
curl -s http://localhost:8501 | grep -q "streamlit" && echo "RUNNING" || echo "FAILED"
kill %1
```
Expected: `RUNNING`

- [ ] **Step 5: Run all new tests to confirm nothing broke**

```bash
pytest tests/test_ui_styles.py tests/test_ui_components.py tests/test_ui_pages_chat.py tests/test_ui_pages_devices.py tests/test_ui_pages_scenes.py tests/test_ui_pages_dashboard.py tests/test_ui_pages_eval_logs.py tests/test_streamlit_app.py -v
```
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat(ui): rewrite streamlit_app.py as option-menu router — enterprise frontend complete"
```

---

## Spec Coverage Check

| Spec Requirement | Covered In |
|---|---|
| Inter font + custom CSS injection | Task 2 |
| Color system (#F5F7FA, #6366F1, #10B981, …) | Task 2 |
| `streamlit-option-menu` sidebar nav | Task 1, 9 |
| Header bar (API status + device count) | Task 3, 4 |
| Chat bubbles (user right, assistant left) | Task 4 |
| Inline tool-call card (✅/❌) | Task 3, 4 |
| 👍👎 feedback buttons (when trace_id present) | Task 4 |
| Device center: 7 cards grouped by room | Task 5 |
| Device card (online/offline/active states) | Task 3, 5 |
| Manual refresh (no polling) | Task 5 |
| Scene page: 3 cards with one-click activate | Task 6 |
| Step-by-step activation feedback | Task 6 |
| Eval dashboard: 4 metric cards | Task 7 |
| RAGAS line chart (Plotly) | Task 7 |
| Intent pie chart (Plotly) | Task 7 |
| Eval logs: searchable table + intent filter | Task 8 |
| RAGAS < 0.6 flagged ⚠️ | Task 8 |
| Row detail: contexts + tool trajectory | Task 8 |
| `plotly>=6.5.0` already present | N/A (already in requirements) |
| `streamlit-option-menu>=0.3.6` added | Task 1 |
