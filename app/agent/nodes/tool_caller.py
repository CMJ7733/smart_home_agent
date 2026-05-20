from app.agent.state import AgentState
from app.tools.device_api import (
    set_temperature, toggle_light, control_curtain, start_robot_vacuum,
)

_TOOL_MAP = {
    "toggle_light": toggle_light,
    "set_temperature": set_temperature,
    "control_curtain": control_curtain,
    "start_robot_vacuum": start_robot_vacuum,
}


def _execute_scene_actions(actions: list[dict]) -> dict:
    """Execute a pre-planned list of tool actions from scene_planner_node."""
    # Re-resolve at call time so unit-test patches on module names take effect.
    tool_map = {
        "toggle_light": toggle_light,
        "set_temperature": set_temperature,
        "control_curtain": control_curtain,
        "start_robot_vacuum": start_robot_vacuum,
    }
    results = []
    for action in actions:
        tool_name = action.get("tool", "")
        args = action.get("args", {})
        tool_fn = tool_map.get(tool_name)
        if not tool_fn:
            results.append({"action": tool_name, "args": args, "result": f"未知工具: {tool_name}"})
            continue
        try:
            result = tool_fn.invoke(args)
            results.append({"action": tool_name, "args": args, "result": str(result)})
        except Exception as e:
            results.append({"action": tool_name, "args": args, "result": f"执行失败: {e}"})
    return {"tool_calls": results}


def tool_caller_node(state: AgentState) -> AgentState:
    """设备工具调用节点: 根据 extracted_entities 调用对应设备 API，或执行 scene_planner 的动作列表"""
    existing = state.get("tool_calls", [])
    if existing and isinstance(existing[0], dict) and "tool" in existing[0]:
        return _execute_scene_actions(existing)

    entities = state.get("extracted_entities", {})
    device = entities.get("device", "")
    room = entities.get("room", "")
    action = entities.get("action", "")
    value = entities.get("value", "")

    tool_calls = []
    try:
        if device in ("灯", "灯光", "灯具"):
            on = action in ("开", "打开", "开启")
            result = toggle_light.invoke({"room": room, "on": on})
        elif device in ("空调", "温度"):
            result = set_temperature.invoke({"room": room, "value": int(value or 24)})
        elif device == "窗帘":
            act = "open" if action in ("开", "打开") else "close"
            result = control_curtain.invoke({"room": room, "action": act})
        elif device in ("扫地机", "扫地机器人"):
            result = start_robot_vacuum.invoke({"room": room})
        else:
            result = f"未识别设备: {device}"
        tool_calls.append({"action": action, "device": device, "args": entities, "result": str(result)})
    except Exception as e:
        tool_calls.append({"action": action, "device": device, "args": entities, "result": f"执行失败: {e}"})

    return {"tool_calls": tool_calls}
