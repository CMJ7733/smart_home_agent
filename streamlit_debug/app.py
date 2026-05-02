# 调试用 Streamlit UI（迁移自根目录 app.py）
# Phase 1 后改为通过 WebSocket 连接 FastAPI，不再直接 import ReactAgent
# 启动命令: streamlit run streamlit_debug/app.py

import json
import streamlit as st
import websocket as ws

# WebSocket 地址（固定）
WS_URL = "ws://localhost:8000/chat/stream/streamlit-session"

st.title("声控未来家Agent（调试模式）")
st.divider()


def send_ws_message(message: str):
    """通过 WebSocket 发送消息并收集响应"""
    results = []
    try:
        sock = ws.create_connection(WS_URL)
        sock.send(json.dumps({"message": message, "user_id": "streamlit-user"}))
        while True:
            msg = sock.recv()
            msg_data = json.loads(msg)
            results.append(msg_data)
            if msg_data.get("type") == "final":
                break
        sock.close()
    except Exception as e:
        results.append({"type": "error", "error": str(e)})
    return results


if "message" not in st.session_state:
    st.session_state["message"] = []

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    with st.spinner("智能家居agent思考中..."):
        messages = send_ws_message(prompt)

        final_response = "（无回复）"
        for msg in messages:
            if msg.get("type") == "final":
                final_response = msg.get("response", "（无响应）")
                break
            elif msg.get("type") == "error":
                final_response = f"错误: {msg.get('error')}"
                break

    st.chat_message("assistant").write(final_response)
    st.session_state["message"].append({"role": "assistant", "content": final_response})
    st.rerun()