import pytest
from unittest.mock import MagicMock, patch
from app.agent.nodes.tool_caller import tool_caller_node


def test_scene_path_executes_action_list():
    """tool_caller_node executes pre-populated scene action list from scene_planner."""
    state = {
        "tool_calls": [
            {"tool": "toggle_light", "args": {"room": "卧室", "on": False}},
        ],
        "extracted_entities": {},
    }
    with patch("app.agent.nodes.tool_caller.toggle_light") as mock_tool:
        mock_tool.invoke.return_value = "卧室灯已关闭"
        result = tool_caller_node(state)

    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["action"] == "toggle_light"
    assert "关闭" in result["tool_calls"][0]["result"]
    mock_tool.invoke.assert_called_once_with({"room": "卧室", "on": False})


def test_scene_path_unknown_tool_returns_error():
    state = {
        "tool_calls": [{"tool": "unknown_tool", "args": {}}],
        "extracted_entities": {},
    }
    result = tool_caller_node(state)
    assert "未知工具" in result["tool_calls"][0]["result"]


def test_device_control_path_unrecognized_device():
    """Empty tool_calls + extracted_entities → device control path."""
    state = {
        "tool_calls": [],
        "extracted_entities": {"device": "冰箱", "room": "厨房", "action": "开", "value": ""},
    }
    result = tool_caller_node(state)
    assert len(result["tool_calls"]) == 1
    assert "未识别设备" in result["tool_calls"][0]["result"]
