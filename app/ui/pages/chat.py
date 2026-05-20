import uuid
from html import escape

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
            safe_content = escape(content)
            if role == "user":
                st.markdown(
                    f'<div style="display:flex;justify-content:flex-end;">'
                    f'<div class="sh-bubble-user">{safe_content}</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="sh-bubble-assistant">{safe_content}</div>',
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
                try:
                    requests.post(
                        f"{API_BASE}/feedback",
                        params={"trace_id": st.session_state.last_trace_id, "feedback": 1},
                        timeout=5,
                    )
                    st.toast("感谢反馈 👍")
                except Exception:
                    st.toast("反馈提交失败", icon="❌")
        with col2:
            if st.button("👎", use_container_width=True, key="fb_down"):
                try:
                    requests.post(
                        f"{API_BASE}/feedback",
                        params={"trace_id": st.session_state.last_trace_id, "feedback": -1},
                        timeout=5,
                    )
                    st.toast("感谢反馈 👎")
                except Exception:
                    st.toast("反馈提交失败", icon="❌")
