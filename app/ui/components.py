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
