# TODO (Phase 1): 设备工具调用节点
# 输入: AgentState.extracted_entities
# 输出: AgentState.tool_calls (已执行动作列表)
# 调用: app/tools/device_api.py, app/tools/scene_api.py
# 复用现有 agent/tools/middleware.py 的 monitor_tool 逻辑接入 LangSmith

from app.agent.state import AgentState
from app.tools.device_api import set_temperature, toggle_light, control_curtain, start_robot_vacuum


def tool_caller_node(state: AgentState) -> AgentState:
    """设备工具调用节点: 根据 extracted_entities 调用对应设备 API"""
    entities = state.get("extracted_entities", {})
    device = entities.get("device", "")
    room = entities.get("room", "")
    action = entities.get("action", "")
    value = entities.get("value", "")

    tool_calls = []
    try:
        if action in ("开", "关", "toggle"):
            result = toggle_light.invoke({"room": room, "on": action == "开"})
        elif action in ("温度", "调温"):
            result = set_temperature.invoke({"room": room, "value": int(value)})
        elif action == "窗帘":
            result = control_curtain.invoke({"room": room, "action": value or "close"})
        elif action == "扫地":
            result = start_robot_vacuum.invoke({"room": room})
        else:
            result = f"未知动作: {action}"
        tool_calls.append({"tool": action, "args": entities, "result": str(result)})
    except Exception as e:
        tool_calls.append({"tool": action, "args": entities, "error": str(e)})

    return {"tool_calls": tool_calls}