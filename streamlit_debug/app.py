# 调试用 Streamlit UI（迁移自根目录 app.py）
# Phase 1 后改为通过 WebSocket 连接 FastAPI，不再直接 import ReactAgent
# 启动命令: streamlit run streamlit_debug/app.py

# TODO (Phase 1): 将现有 app.py 中的 UI 逻辑迁移至此，
#                 并将 ReactAgent.execute_stream() 替换为 WebSocket 客户端调用

import streamlit as st

st.title("智能家居 Agent（调试模式）")
st.info("Phase 1 完成后，此 UI 将通过 WebSocket 连接 FastAPI 接口。")
