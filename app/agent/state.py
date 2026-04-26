from typing import Literal, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    session_id: str
    user_id: str
    user_input: str
    chat_history: Annotated[list[BaseMessage], add_messages]
    extracted_entities: dict           # {device, room, action, value}
    retrieved_context: list[str]       # RAG 召回文档
    current_intent: Literal["chitchat", "device_control", "kb_query", "scene", "report"]
    tool_calls: list[dict]             # 已执行的设备动作
    final_response: str
    trace_id: str                      # 关联 LangSmith trace / 评估日志
