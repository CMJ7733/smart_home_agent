# TODO (Phase 1): 统一回复组装节点
# 输入: AgentState (retrieved_context / tool_calls / current_intent 等)
# 输出: AgentState.final_response (str)
# 说明: 负责将各节点产出整合为最终自然语言回复，调用 main_prompt.txt

from app.agent.state import AgentState


def responder_node(state: AgentState) -> AgentState:
    """统一回复组装节点 (Phase 1 占位)"""
    retrieved = state.get("retrieved_context", [])
    context_str = "\n".join(retrieved) if retrieved else "无相关上下文"
    return {"final_response": f"[Phase 1 占位] 检索到 {len(retrieved)} 条相关文档:\n{context_str}"}
