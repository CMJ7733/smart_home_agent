# TODO (Phase 1): 意图路由节点
# 输入: AgentState.user_input
# 输出: AgentState.current_intent (枚举: chitchat / device_control / kb_query / scene / report)
# 实现: LLM + few-shot router_prompt.txt，替代 ReAct 自主决策，保证路由确定性

from app.agent.state import AgentState


def router_node(state: AgentState) -> AgentState:
    raise NotImplementedError("Phase 1: 待实现意图路由节点")
