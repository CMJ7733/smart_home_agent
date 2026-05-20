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
