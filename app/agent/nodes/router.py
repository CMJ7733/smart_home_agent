# TODO (Phase 1): 意图路由节点
# 输入: AgentState.user_input
# 输出: AgentState.current_intent (枚举: chitchat / device_control / kb_query / scene / report)
# 实现: LLM + few-shot router_prompt.txt，替代 ReAct 自主决策，保证路由确定性

import os
from app.agent.state import AgentState


def router_node(state: AgentState) -> AgentState:
    # 测试模式: 优先使用环境变量或已存在的意图，快速跳过路由
    test_intent = os.environ.get("TEST_INTENT")
    if test_intent:
        return {"current_intent": test_intent}

    # 如果 state 中已有意图（如测试时直接传入），直接使用
    existing_intent = state.get("current_intent")
    if existing_intent:
        return {"current_intent": existing_intent}

    raise NotImplementedError("Phase 1: 待实现意图路由节点 (LLM + few-shot)")
