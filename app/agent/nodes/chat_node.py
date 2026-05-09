# TODO (Phase 1): 闲聊节点
# 输入: AgentState.user_input + AgentState.chat_history
# 输出: AgentState.final_response
# 说明: 非家居控制类对话的兜底节点，直接调用 LLM 生成回复

from app.agent.state import AgentState
from model.factory import chat_model
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "main_prompt.txt"


def _load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def chat_node(state: AgentState) -> AgentState:
    """闲聊节点: 调用 LLM 生成回复"""
    system_prompt = _load_prompt()
    messages = [SystemMessage(content=system_prompt)]

    for msg in state.get("chat_history", []):
        if hasattr(msg, "type"):
            if msg.type == "human":
                messages.append(HumanMessage(content=msg.content))
            elif msg.type == "ai":
                messages.append(AIMessage(content=msg.content))
        else:
            messages.append(HumanMessage(content=msg.content))

    messages.append(HumanMessage(content=state["user_input"]))
    response = chat_model.invoke(messages)
    return {"final_response": response.content}