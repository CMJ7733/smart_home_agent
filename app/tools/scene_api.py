# TODO (Phase 1): 场景模式接口
# 场景 = 一组预设设备动作的组合，由 scene_planner_node 调用
# 内置场景模板（可扩展）：睡眠模式 / 离家模式 / 观影模式 / 起床模式

from langchain_core.tools import tool

SCENE_TEMPLATES: dict[str, list[dict]] = {
    "睡眠模式": [
        {"tool": "toggle_light", "args": {"room": "卧室", "on": False}},
        {"tool": "set_temperature", "args": {"room": "卧室", "value": 26}},
        {"tool": "control_curtain", "args": {"room": "卧室", "action": "close"}},
    ],
    "离家模式": [
        {"tool": "toggle_light", "args": {"room": "全屋", "on": False}},
        {"tool": "control_curtain", "args": {"room": "全屋", "action": "close"}},
    ],
    "观影模式": [
        {"tool": "toggle_light", "args": {"room": "客厅", "on": True, "color": "暖色", "brightness": 20}},
        {"tool": "control_curtain", "args": {"room": "客厅", "action": "close"}},
    ],
}


@tool(description="执行预设场景模式，scene_name: 场景名称（如：睡眠模式、离家模式、观影模式）")
def activate_scene(scene_name: str) -> str:
    actions = SCENE_TEMPLATES.get(scene_name)
    if actions is None:
        available = "、".join(SCENE_TEMPLATES.keys())
        return f"未找到场景 '{scene_name}'，可用场景：{available}"

    from app.tools.device_api import toggle_light, set_temperature, control_curtain, start_robot_vacuum
    tool_map = {
        "toggle_light": toggle_light,
        "set_temperature": set_temperature,
        "control_curtain": control_curtain,
        "start_robot_vacuum": start_robot_vacuum,
    }

    results = []
    for action in actions:
        tool_fn = tool_map.get(action.get("tool", ""))
        if not tool_fn:
            results.append(f"未知工具: {action.get('tool')}")
            continue
        try:
            results.append(str(tool_fn.invoke(action.get("args", {}))))
        except Exception as e:
            results.append(f"{action.get('tool')} 失败: {e}")

    return f"{scene_name}已激活：" + "；".join(results)
