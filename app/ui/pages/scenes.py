import streamlit as st
from app.ui.components import scene_card

SCENES = [
    {
        "name": "睡眠模式",
        "icon": "🌙",
        "summary": "关卧室灯 · 空调调至 26°C · 关卧室窗帘",
    },
    {
        "name": "离家模式",
        "icon": "🚪",
        "summary": "关全屋灯 · 关全屋窗帘",
    },
    {
        "name": "观影模式",
        "icon": "🎬",
        "summary": "客厅暖光 20% · 关客厅窗帘",
    },
]


def render() -> None:
    st.markdown("## 场景控制")
    st.markdown(
        '<p style="color:#64748B;font-size:14px;margin-bottom:20px;">'
        "一键激活预设场景，所有设备同步执行</p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(SCENES))
    for col, scene in zip(cols, SCENES):
        with col:
            scene_card(scene["name"], scene["icon"], scene["summary"])
            if st.button(
                "一键激活",
                key=f"activate_{scene['name']}",
                use_container_width=True,
                type="primary",
            ):
                _run_scene(scene["name"])


def _run_scene(scene_name: str) -> None:
    from app.tools.scene_api import SCENE_TEMPLATES
    from app.tools.device_api import toggle_light, set_temperature, control_curtain, start_robot_vacuum

    actions = SCENE_TEMPLATES.get(scene_name, [])
    status_placeholder = st.empty()

    step_results: list[str] = []
    tool_map = {
        "toggle_light": toggle_light,
        "set_temperature": set_temperature,
        "control_curtain": control_curtain,
        "start_robot_vacuum": start_robot_vacuum,
    }

    with st.spinner(f"正在激活「{scene_name}」…"):
        for action in actions:
            fn = tool_map.get(action.get("tool", ""))
            if not fn:
                step_results.append(f"❌ 未知工具: {action.get('tool')}")
                continue
            try:
                result = fn.invoke(action.get("args", {}))
                step_results.append(f"✅ {result}")
            except Exception as e:
                step_results.append(f"❌ 失败: {e}")
            status_placeholder.markdown("\n\n".join(step_results))

    status_placeholder.success(f"✅ 场景「{scene_name}」激活完成")
    for line in step_results:
        st.markdown(f"- {line}")
