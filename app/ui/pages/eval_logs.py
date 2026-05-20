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
        logs = [l for l in logs if search.lower() in l.get("query", "").lower()]
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
            "查询摘要": log.get("query", "")[:60],
            "意图": log.get("intent", "-"),
            "反馈": _feedback_label(log.get("user_feedback")),
            "RAGAS 分": score_str,
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Detail view
    idx = st.selectbox(
        "选择行号查看详情",
        options=range(len(logs)),
        format_func=lambda i: f"#{i} — {(logs[i].get('query') or '')[:50]}",
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
                if isinstance(contexts, list):
                    for ctx in contexts:
                        st.markdown(f"- {ctx[:120]}")
                else:
                    st.write("-")
            except Exception:
                st.write("-")

            st.markdown("**Tool Calls 轨迹**")
            try:
                traj = json.loads(log.get("trajectory_json", "[]"))
                if isinstance(traj, list):
                    for t in traj:
                        st.json(t)
                else:
                    st.write("-")
            except Exception:
                st.write("-")

        if log.get("eval_metrics_json"):
            st.markdown("**RAGAS 指标**")
            try:
                st.json(json.loads(log["eval_metrics_json"]))
            except Exception:
                pass
