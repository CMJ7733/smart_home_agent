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
