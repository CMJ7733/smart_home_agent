# TODO (Phase 1): 设备实体抽取节点
# 输入: AgentState.user_input + AgentState.chat_history
# 输出: AgentState.extracted_entities = {device, room, action, value}
# 说明: 需处理模糊指代（"老样子"→查长期记忆补全），Phase 2 接入 memory_graph

from app.agent.state import AgentState
from model.factory import chat_model
import json, re
from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "entity_extract_prompt.txt"


def _load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def entity_extractor_node(state: AgentState) -> AgentState:
    """实体抽取节点: 从用户输入提取设备/房间/动作/值"""
    user_input = state["user_input"]
    prompt_template = _load_prompt()
    prompt = prompt_template.replace("{user_input}", user_input)
    messages = [{"role": "user", "content": prompt}]
    response = chat_model.invoke(messages)
    match = re.search(r'\{[^}]+\}', response.content, re.DOTALL)
    entities = json.loads(match.group()) if match else {}
    return {"extracted_entities": entities}