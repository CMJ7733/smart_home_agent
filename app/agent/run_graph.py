"""
独立测试入口：python -m app.agent.run_graph
验证 LangGraph 状态机拓扑和各分支是否正常工作。
"""
from app.agent.graph import graph
from app.agent.state import AgentState


TEST_CASES = [
    {"user_input": "把卧室空调调到24度",          "expected": "device_control"},
    {"user_input": "扫地机器人滚刷不转怎么办",      "expected": "kb_query"},
    {"user_input": "睡眠模式",                     "expected": "scene"},
    {"user_input": "今天天气怎么样？",              "expected": "chitchat"},
    {"user_input": "帮我生成5月使用报告",           "expected": "report"},
]


def run():
    print("=" * 60)
    print("LangGraph Smart Home Agent — 路由测试")
    print("=" * 60)

    for case in TEST_CASES:
        state: AgentState = {
            "session_id":  "test-session",
            "user_id":     "test-user",
            "user_input":  case["user_input"],
            "chat_history": [],
            "extracted_entities": {},
            "retrieved_context": [],
            "current_intent": "",
            "tool_calls":      [],
            "final_response":  "",
            "trace_id":        "trace-test",
        }

        result = graph.invoke(state)
        intent = result.get("current_intent", "?")
        status = "✓" if intent == case["expected"] else "✗"
        print(f"{status} [{intent}] (预期: {case['expected']}) — {case['user_input']}")

        if result.get("tool_calls"):
            for tc in result["tool_calls"]:
                print(f"    → {tc['action']}: {tc.get('result', '')}")
        if result.get("final_response"):
            print(f"    回复: {result['final_response'][:60]}...")
        print()


if __name__ == "__main__":
    run()
