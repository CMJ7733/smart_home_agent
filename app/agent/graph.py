# TODO (Phase 1): 用 LangGraph StateGraph 替代 ReAct Agent
#
# 状态机拓扑:
#   START → [router] → chitchat      → [chat_node]    → END
#                    → kb_query      → [rag_node]     → [responder] → END
#                    → device_control→ [entity_extractor] → [tool_caller] → [responder] → END
#                    → scene         → [scene_planner]    → [tool_caller] → [responder] → END
#                    → report        → [report_subgraph]  → END
#   每条路径末尾均异步触发 [memory_writer]
#
# 依赖: app/agent/nodes/ 下各节点; app/agent/state.py 中的 AgentState

from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState


def build_graph():
    raise NotImplementedError("Phase 1: 待实现 LangGraph 状态机")


graph = None  # Phase 1 实现后替换为 build_graph().compile()
