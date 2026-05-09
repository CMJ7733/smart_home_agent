import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Smart Home Agent", layout="wide")

API_BASE = "http://localhost:8000/api/v1"

st.sidebar.title("⚙️ 配置")
st.sidebar.write("**当前配置**")
st.sidebar.write(f"API: {API_BASE}")

# 初始化 session state
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = "user-001"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_trace_id" not in st.session_state:
    st.session_state.last_trace_id = ""

# 侧栏设置
st.sidebar.text_input("User ID", value=st.session_state.user_id, key="user_id_input")
st.session_state.user_id = st.session_state.user_id_input

st.sidebar.write(f"**Session ID**: `{st.session_state.session_id}`")

# 标签页
tab1, tab2, tab3 = st.tabs(["💬 对话", "📊 评估看板", "📝 Eval Logs"])

with tab1:
    st.title("🏠 Smart Home Agent")

    # 对话历史
    chat_container = st.container(height=400, border=True)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant" and msg.get("meta"):
                    meta = msg["meta"]
                    with st.expander("📋 详情"):
                        st.write(f"**意图**: {meta.get('intent', '-')}")
                        st.write(f"**Trace ID**: `{meta.get('trace_id', '-')}`")
                        if meta.get("tool_calls"):
                            st.write("**设备操作**:")
                            for tc in meta["tool_calls"]:
                                st.write(f"  - {tc.get('action')}({tc.get('device')}): {tc.get('result', '-')}")

    # 输入区域
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.chat_input("输入问题...")
    with col2:
        if st.button("🔄 清空", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # 发送消息
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("思考中..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/chat",
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id,
                        "user_id": st.session_state.user_id,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                st.session_state.last_trace_id = data.get("trace_id", "")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data.get("response", "（无响应）"),
                    "meta": {
                        "intent": data.get("intent", ""),
                        "trace_id": data.get("trace_id", ""),
                    }
                })
            except Exception as e:
                st.error(f"请求失败: {e}")

        st.rerun()

    # 反馈区域
    if st.session_state.last_trace_id:
        st.divider()
        st.write("**反馈**")
        feedback_col1, feedback_col2 = st.columns(2)
        with feedback_col1:
            if st.button("👍 赞", use_container_width=True):
                requests.post(
                    f"{API_BASE}/feedback",
                    params={"trace_id": st.session_state.last_trace_id, "feedback": 1}
                )
                st.success("反馈已提交")
        with feedback_col2:
            if st.button("👎 踩", use_container_width=True):
                requests.post(
                    f"{API_BASE}/feedback",
                    params={"trace_id": st.session_state.last_trace_id, "feedback": -1}
                )
                st.success("反馈已提交")

with tab2:
    st.title("📊 评估看板")

    days = st.slider("时间范围（天）", 1, 30, 7)

    try:
        resp = requests.get(f"{API_BASE}/eval/dashboard", params={"days": days})
        resp.raise_for_status()
        dashboard = resp.json()

        # 总体统计
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总对话轮数", dashboard.get("total_turns", 0))
        with col2:
            st.metric("Bad Cases", dashboard.get("bad_case_count", 0))
        with col3:
            st.metric("👍 赞", dashboard.get("feedback_stats", {}).get("thumbs_up", 0))
        with col4:
            st.metric("👎 踩", dashboard.get("feedback_stats", {}).get("thumbs_down", 0))

        # 日均指标
        daily_metrics = dashboard.get("daily_metrics", {})
        if daily_metrics:
            st.subheader("📈 日均评估指标")
            metric_data = []
            for day in sorted(daily_metrics.keys()):
                metrics = daily_metrics[day]
                metric_data.append({
                    "日期": day,
                    "Faithfulness": metrics.get("faithfulness", 0),
                    "Answer Relevancy": metrics.get("answer_relevancy", 0),
                    "Context Precision": metrics.get("context_precision", 0),
                })
            st.dataframe(metric_data, use_container_width=True)
        else:
            st.info("暂无评估数据（需要先运行 RAGAS）")

    except Exception as e:
        st.error(f"获取看板数据失败: {e}")

with tab3:
    st.title("📝 Eval Logs")

    try:
        from app.db.eval_log_repo import EvalLogRepo
        repo = EvalLogRepo()
        logs = repo.query_recent(7)

        if logs:
            st.write(f"最近 7 天共 {len(logs)} 条记录")

            for log in reversed(logs[-10:]):  # 只显示最近 10 条
                with st.expander(f"{log['created_at'][:10]} | {log['intent']} | {log['query'][:50]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**基本信息**")
                        st.write(f"- Trace ID: `{log['trace_id']}`")
                        st.write(f"- User: {log['user_id']}")
                        st.write(f"- Intent: {log['intent']}")
                    with col2:
                        st.write("**评估结果**")
                        if log["eval_metrics_json"]:
                            metrics = json.loads(log["eval_metrics_json"])
                            for k, v in metrics.items():
                                st.write(f"- {k}: {v:.3f}" if isinstance(v, float) else f"- {k}: {v}")
                        else:
                            st.write("- 暂无评估")

                    st.write("**查询**")
                    st.write(log["query"])
                    st.write("**回复**")
                    st.write(log["response"])

                    st.write("**反馈**")
                    feedback_val = log.get("user_feedback")
                    if feedback_val == 1:
                        st.success("👍 用户赞")
                    elif feedback_val == -1:
                        st.error("👎 用户踩")
                    else:
                        st.write("无反馈")
        else:
            st.info("暂无 Eval Logs")

    except Exception as e:
        st.error(f"加载 Eval Logs 失败: {e}")
