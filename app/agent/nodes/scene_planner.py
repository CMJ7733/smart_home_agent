# TODO (Phase 1): 场景规划节点（多设备编排）
# 输入: AgentState.user_input + AgentState.extracted_entities
# 输出: AgentState.tool_calls (多个设备动作的有序列表)
# 示例: "睡眠模式" → [{关灯, 卧室}, {降温, 25度}, {拉窗帘, 卧室}]
# 复用: app/tools/scene_api.py 中的场景模板

from app.agent.state import AgentState
from app.tools.scene_api import SCENE_TEMPLATES

SCENE_KEYWORDS = {
    "睡眠模式": "睡眠",
    "离家模式": "离家",
    "观影模式": "观影",
    "起床模式": "起床",
}


def scene_planner_node(state: AgentState) -> AgentState:
    """场景规划节点: 匹配用户输入中的场景关键词，返回预设动作列表"""
    user_input = state.get("user_input", "")
    for name, keyword in SCENE_KEYWORDS.items():
        if keyword in user_input:
            return {"tool_calls": SCENE_TEMPLATES.get(name, [])}
    return {"tool_calls": []}