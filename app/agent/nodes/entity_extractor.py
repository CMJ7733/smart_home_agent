# TODO (Phase 1): 设备实体抽取节点
# 输入: AgentState.user_input + AgentState.chat_history
# 输出: AgentState.extracted_entities = {device, room, action, value}
# 说明: 需处理模糊指代（"老样子"→查长期记忆补全），Phase 2 接入 memory_graph

from app.agent.state import AgentState


def entity_extractor_node(state: AgentState) -> AgentState:
    raise NotImplementedError("Phase 1: 待实现实体抽取节点")
