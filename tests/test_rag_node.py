"""
测试 rag_node 链路: router → rag → responder → memory_writer → END

用法:
    $env:TEST_INTENT="kb_query"
    python -m tests.test_rag_node
"""

import os
from app.agent.graph import graph
from app.agent.state import AgentState

# 设置测试意图，跳过 router 的 LLM 调用
os.environ["TEST_INTENT"] = "kb_query"


def test_rag_node_chain():
    """测试 kb_query 路径: router → rag → responder → memory_writer → END"""
    state: AgentState = {
        "session_id": "test-001",
        "user_id": "test-user",
        "user_input": "如何连接空调？",
        "chat_history": [],
        "extracted_entities": {},
        "retrieved_context": [],
        "current_intent": "kb_query",
        "tool_calls": [],
        "final_response": "",
        "trace_id": "test-trace",
    }

    result = graph.invoke(state)

    print(f"\n--- test_rag_node_chain result ---")
    print(f"retrieved_context count: {len(result.get('retrieved_context', []))}")
    print(f"retrieved_context[0]: {result.get('retrieved_context', [''])[0][:100] if result.get('retrieved_context') else 'N/A'}")
    print(f"final_response: {result.get('final_response', '')}[:200]")


if __name__ == "__main__":
    test_rag_node_chain()