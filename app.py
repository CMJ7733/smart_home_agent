import time

import streamlit as st
from app.agent.graph import graph
from app.agent.state import AgentState

# 标题
st.title("声控未来家Agent")
st.divider()

if "agent" not in st.session_state:
    st.session_state["agent"] = graph

if "message" not in st.session_state:
    st.session_state["message"] = []

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

# 用户输入提示词
prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    response_messages = []
    with st.spinner("智能家居agent思考中..."):
        # 构建初始状态
        state: AgentState = {
            "session_id": "streamlit-session",
            "user_id": "streamlit-user",
            "user_input": prompt,
            "chat_history": [],
            "extracted_entities": {},
            "retrieved_context": [],
            "current_intent": "",  # router_node 会自动推断
            "tool_calls": [],
            "final_response": "",
            "trace_id": "streamlit-trace",
        }

        result = st.session_state["agent"].invoke(state)
        final_response = result.get("final_response", "（无回复）")

        st.chat_message("assistant").write(final_response)
        st.session_state["message"].append({"role": "assistant", "content": final_response})
        st.rerun()