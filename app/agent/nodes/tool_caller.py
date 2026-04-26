# TODO (Phase 1): 设备工具调用节点
# 输入: AgentState.extracted_entities
# 输出: AgentState.tool_calls (已执行动作列表)
# 调用: app/tools/device_api.py, app/tools/scene_api.py
# 复用现有 agent/tools/middleware.py 的 monitor_tool 逻辑接入 LangSmith

from app.agent.state import AgentState


def tool_caller_node(state: AgentState) -> AgentState:
    raise NotImplementedError("Phase 1: 待实现工具调用节点")
