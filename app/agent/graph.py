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
from app.agent.nodes import (
    router_node,
    chat_node,
    rag_node,
    entity_extractor_node,
    tool_caller_node,
    scene_planner_node,
    responder_node,
    memory_writer_node,
)


def build_graph() -> StateGraph:
    """构建 LangGraph 状态机"""
    graph = StateGraph(AgentState)

    # 注册节点
    graph.add_node("router", router_node)
    graph.add_node("chat", chat_node)
    graph.add_node("rag", rag_node)
    graph.add_node("entity_extractor", entity_extractor_node)
    graph.add_node("tool_caller", tool_caller_node)
    graph.add_node("scene_planner", scene_planner_node)
    graph.add_node("responder", responder_node)
    graph.add_node("memory_writer", memory_writer_node)

    # 起点
    graph.add_edge(START, "router")

    # 意图路由分支
    def route_intent(state: AgentState) -> str:
        return state.get("current_intent", "chitchat")

    graph.add_conditional_edges(
        "router",
        route_intent,
        {
            "chitchat": "chat",
            "kb_query": "rag",
            "device_control": "entity_extractor",
            "scene": "scene_planner",
            "report": END,  # report 直接结束（TODO: report_subgraph）
        },
    )

    # chitchat 路径: chat → memory_writer → END
    graph.add_edge("chat", "memory_writer")
    graph.add_edge("memory_writer", END)

    # kb_query 路径: rag → responder → memory_writer → END
    graph.add_edge("rag", "responder")
    graph.add_edge("responder", "memory_writer")
    graph.add_edge("memory_writer", END)

    # device_control 路径: entity_extractor → tool_caller → responder → memory_writer → END
    graph.add_edge("entity_extractor", "tool_caller")
    graph.add_edge("tool_caller", "responder")
    graph.add_edge("responder", "memory_writer")
    graph.add_edge("memory_writer", END)

    # scene 路径: scene_planner → tool_caller → responder → memory_writer → END
    graph.add_edge("scene_planner", "tool_caller")
    graph.add_edge("tool_caller", "responder")
    graph.add_edge("responder", "memory_writer")
    graph.add_edge("memory_writer", END)

    return graph


graph = build_graph().compile()

