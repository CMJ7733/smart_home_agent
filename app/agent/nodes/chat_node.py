# TODO (Phase 1): 闲聊节点
# 输入: AgentState.user_input + AgentState.chat_history
# 输出: AgentState.final_response
# 说明: 非家居控制类对话的兜底节点，直接调用 LLM 生成回复

from app.agent.state import AgentState


def chat_node(state: AgentState) -> AgentState:
    raise NotImplementedError("Phase 1: 待实现闲聊节点")
