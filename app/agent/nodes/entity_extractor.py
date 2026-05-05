# TODO (Phase 1): 设备实体抽取节点
# 输入: AgentState.user_input + AgentState.chat_history
# 输出: AgentState.extracted_entities = {device, room, action, value}
# Phase 2: 接入 memory_graph，模糊指代时调用 query_preferences 补全

from app.agent.state import AgentState
from app.memory.memory_graph import get_memory_graph
from model.factory import chat_model
import json, re, logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "entity_extract_prompt.txt"

_AMBIGUITY_KEYWORDS = {
    "老样子", "跟之前一样", "按惯例", "像以前", "老规矩",
    "和原来一样", "还是老样子", "照旧", "依旧", "一如既往",
    "按平时", "按习惯", "平常那样",
}


def _is_ambiguous(text: str) -> bool:
    return any(kw in text for kw in _AMBIGUITY_KEYWORDS)


def _load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def entity_extractor_node(state: AgentState) -> AgentState:
    """实体抽取节点: 从用户输入提取设备/房间/动作/值"""
    user_input = state["user_input"]
    user_id = state.get("user_id", "")
    prompt_template = _load_prompt()
    messages = [
        {"role": "system", "content": prompt_template},
        {"role": "user", "content": f"请从以下用户输入中提取实体：{user_input}"},
    ]
    response = chat_model.invoke(messages)

    # 兼容 markdown 代码块格式 ```json ... ```
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1] or content.split("```")[2] or content
    content = content.strip()

    # 使用 JSONDecoder 解析，支持嵌套 JSON
    try:
        decoder = json.JSONDecoder()
        entities, _ = decoder.raw_decode(content)
    except (json.JSONDecodeError, ValueError):
        logger.warning(f"[EntityExtractor] LLM response is not valid JSON: {response.content[:200]}")
        entities = {}

    # Phase 2: resolve ambiguous references using long-term memory
    if _is_ambiguous(user_input) and user_id:
        prefs = get_memory_graph().query_preferences(user_id)
        if prefs:
            if not entities.get("value"):
                entities.setdefault("device", "")
                entities.setdefault("room", "")
                entities.setdefault("action", "")
                # Fill in missing values from preferences
                if prefs.get("room_temp_preference"):
                    entities["value"] = prefs["room_temp_preference"]
                elif prefs.get("light_color_preference"):
                    entities["value"] = prefs["light_color_preference"]
                elif prefs.get("light_brightness_preference"):
                    entities["value"] = prefs["light_brightness_preference"]
                elif prefs.get("curtain_preference"):
                    entities["value"] = prefs["curtain_preference"]
                elif prefs.get("vacuum_preference"):
                    entities["value"] = prefs["vacuum_preference"]

    return {"extracted_entities": entities}