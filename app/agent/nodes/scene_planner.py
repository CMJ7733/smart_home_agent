# TODO (Phase 1): 场景规划节点（多设备编排）
# 输入: AgentState.user_input + AgentState.extracted_entities
# 输出: AgentState.tool_calls (多个设备动作的有序列表)
# 示例: "睡眠模式" → [{关灯, 卧室}, {降温, 25度}, {拉窗帘, 卧室}]
# 复用: app/tools/scene_api.py 中的场景模板

from app.agent.state import AgentState


def scene_planner_node(state: AgentState) -> AgentState:
    raise NotImplementedError("Phase 1: 待实现场景规划节点")
