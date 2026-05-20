# TODO (Phase 1): 意图路由节点
# 输入: AgentState.user_input
# 输出: AgentState.current_intent (枚举: chitchat / device_control / kb_query / scene / report)
# 实现: LLM + few-shot router_prompt.txt，替代 ReAct 自主决策，保证路由确定性

import os
from app.agent.state import AgentState

KEYWORD_INTENTS = {
    "如何": "kb_query",
    "怎么": "kb_query",
    "知识库": "kb_query",
    "连接": "kb_query",
    "是什么": "kb_query",
    "介绍一下": "kb_query",
    "开": "device_control",
    "关": "device_control",
    "温度": "device_control",
    "调温": "device_control",
    "调到": "device_control",
    "空调": "device_control",
    "窗帘": "device_control",
    "扫地": "device_control",
    "亮度": "device_control",
    "灯": "device_control",
    "模式": "scene",
    "睡眠": "scene",
    "离家": "scene",
    "观影": "scene",
    "起床": "scene",
}


def router_node(state: AgentState) -> AgentState:
    """意图路由节点: 关键词规则路由（Phase 1 占位，Phase 2 替换为 LLM few-shot）"""
    # 测试模式: 优先使用环境变量或已存在的意图
    # test_intent = os.environ.get("TEST_INTENT")
    # if test_intent:
    #     return {"current_intent": test_intent}

    # 如果 state 中已有意图（如测试时直接传入），直接使用
    existing_intent = state.get("current_intent")
    if existing_intent:
        return {"current_intent": existing_intent}

    # 关键词规则路由
    user_input = state.get("user_input", "")
    for keyword, intent in KEYWORD_INTENTS.items():
        if keyword in user_input:
            return {"current_intent": intent}

    return {"current_intent": "chitchat"}