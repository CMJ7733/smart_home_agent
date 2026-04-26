# TODO (Phase 1): 统一回复组装节点
# 输入: AgentState (retrieved_context / tool_calls / current_intent 等)
# 输出: AgentState.final_response (str)
# 说明: 负责将各节点产出整合为最终自然语言回复，调用 main_prompt.txt

from app.agent.state import AgentState


def responder_node(state: AgentState) -> AgentState:
    raise NotImplementedError("Phase 1: 待实现回复节点")
