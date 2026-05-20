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
