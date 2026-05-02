# TODO (Phase 1): 统一回复组装节点
# 输入: AgentState (retrieved_context / tool_calls / current_intent 等)
# 输出: AgentState.final_response (str)
# 说明: 负责将各节点产出整合为最终自然语言回复，调用 prompts/main_prompt.txt

from app.agent.state import AgentState
from model.factory import chat_model
from pathlib import Path

RAG_SUMMARIZE_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "rag_summarize.txt"


def _load_prompt() -> str:
    with open(RAG_SUMMARIZE_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def responder_node(state: AgentState) -> AgentState:
    """统一回复组装节点: 根据 current_intent 组合各路径状态生成最终回复"""
    intent = state.get("current_intent", "")
    retrieved = state.get("retrieved_context", [])
    tool_calls = state.get("tool_calls", [])

    if intent == "kb_query":
        context = "\n".join(retrieved) if retrieved else "无相关文档"
        # 使用 rag_summarize.txt 的 prompt 让 LLM 总结
        prompt_template = _load_prompt()
        prompt = prompt_template.replace("{input}", state.get("user_input", "")).replace("{context}", context)
        messages = [{"role": "user", "content": prompt}]
        response = chat_model.invoke(messages)
        return {"final_response": response.content}
    elif intent == "device_control":
        actions = ", ".join([f"{tc.get('tool')}" for tc in tool_calls])
        return {"final_response": f"已完成以下操作：{actions}"}
    elif intent == "scene":
        scene_name = next(
            (name for name, kw in {"睡眠模式": "睡眠", "离家模式": "离家", "观影模式": "观影", "起床模式": "起床"}.items()
             if kw in state.get("user_input", "")), None
        )
        prefix = f"已启动{scene_name}，" if scene_name else "场景已执行，"
        actions = ", ".join([f"{tc.get('tool')}" for tc in tool_calls]) if tool_calls else "无设备动作"
        return {"final_response": f"{prefix}执行了以下动作：{actions}"}
    elif intent == "chitchat":
        return {"final_response": state.get("final_response", "好的")}
    return {"final_response": "收到您的请求，正在处理中。"}