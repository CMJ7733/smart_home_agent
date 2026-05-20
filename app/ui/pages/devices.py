import streamlit as st
from app.ui.components import header_bar, device_card, status_badge
from app.tools.device_registry import DeviceRegistry
from app.tools.iotda_client import IotdaClient
from app.core.config import get_settings

DEVICE_ICONS = {
    "light":   "💡",
    "ac":      "❄️",
    "curtain": "🪟",
    "vacuum":  "🤖",
}

DEVICE_NAMES = {
    "light":   "灯光",
    "ac":      "空调",
    "curtain": "窗帘",
    "vacuum":  "扫地机器人",
}

ROOM_ORDER = ["卧室", "客厅", "全屋"]


def _load_shadows(devices: list[dict]) -> dict[str, dict]:
    """Returns {device_id: shadow_properties_dict}. Never raises."""
    s = get_settings()
    client = IotdaClient(s.iotda_endpoint, s.iotda_project_id, s.iotda_ak, s.iotda_sk)
    result = {}
    for dev in devices:
        try:
            shadow = client.get_device_shadow(dev["device_id"])
            items = shadow.get("shadow", [])
            props = items[0].get("reported", {}).get("properties", {}) if items else {}
            status = shadow.get("device_status", "OFFLINE")
            result[dev["device_id"]] = {"online": status == "ONLINE", **props}
        except Exception:
            result[dev["device_id"]] = {"online": False}
    return result


def render() -> None:
    registry = DeviceRegistry()
    all_devs = registry.all_devices()

    if "device_shadows" not in st.session_state:
        st.session_state.device_shadows = {}

    col_title, col_btn = st.columns([5, 1])
    with col_title:
        online_count = sum(
            1 for d in all_devs
            if st.session_state.device_shadows.get(d["device_id"], {}).get("online", False)
        )
        st.markdown(
            f"## 设备中心 "
            f'<span class="sh-badge-online">{online_count} 在线</span>',
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("🔄 刷新", use_container_width=True):
            st.session_state.device_shadows = _load_shadows(all_devs)
            st.rerun()

    if not st.session_state.device_shadows:
        st.info("点击「刷新」加载设备状态")
        return

    # Group devices by room
    rooms: dict[str, list[dict]] = {}
    for dev in all_devs:
        rooms.setdefault(dev["room"], []).append(dev)

    for room in ROOM_ORDER:
        if room not in rooms:
            continue
        st.markdown(f"### {room}")
        cols = st.columns(len(rooms[room]))
        for col, dev in zip(cols, rooms[room]):
            with col:
                shadow = st.session_state.device_shadows.get(dev["device_id"], {})
                online = shadow.get("online", False)
                on = shadow.get("on", False) if dev["type"] != "vacuum" else False
                display_props = {k: v for k, v in shadow.items() if k not in ("online", "on")}
                device_card(
                    name=f"{room}{DEVICE_NAMES.get(dev['type'], dev['type'])}",
                    icon=DEVICE_ICONS.get(dev["type"], "📱"),
                    online=online,
                    on=on,
                    properties=display_props,
                )
