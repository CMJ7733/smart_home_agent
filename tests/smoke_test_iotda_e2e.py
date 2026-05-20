"""
IoTDA End-to-End Smoke Test
===========================
Hits real Huawei IoTDA cloud hardware via REST + MQTT (device simulator must be running).
Do NOT mock anything in this script.

Run with:
    python tests/smoke_test_iotda_e2e.py
"""

import sys
import os
import asyncio
import uuid
from pathlib import Path

# Ensure project root is on sys.path so `app`, `model`, `utils`, etc. resolve
# regardless of which directory the script is invoked from.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# load_dotenv MUST be called before any project imports that use get_settings()
from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

# --------------------------------------------------------------------------- #
# Project imports (after dotenv)
# --------------------------------------------------------------------------- #
from app.tools.device_api import (
    toggle_light,
    set_temperature,
    control_curtain,
    start_robot_vacuum,
)
from app.tools.iotda_client import IotdaClient
from app.tools.device_registry import DeviceRegistry
from app.core.config import get_settings
from app.agent.graph import graph
from app.agent.state import AgentState

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _make_state(user_input: str) -> AgentState:
    return AgentState(
        session_id=f"smoke-{uuid.uuid4().hex[:8]}",
        user_id="smoke_tester",
        user_input=user_input,
        chat_history=[],
        extracted_entities={},
        retrieved_context=[],
        current_intent="",
        tool_calls=[],
        final_response="",
        trace_id=f"smoke-trace-{uuid.uuid4().hex[:8]}",
    )


def _get_iotda_client() -> IotdaClient:
    s = get_settings()
    return IotdaClient(s.iotda_endpoint, s.iotda_project_id, s.iotda_ak, s.iotda_sk)


def _get_registry() -> DeviceRegistry:
    return DeviceRegistry()


def _get_shadow_properties(device_id: str) -> dict:
    """Return the first service's reported properties from device shadow."""
    client = _get_iotda_client()
    shadow = client.get_device_shadow(device_id)
    shadow_items = shadow.get("shadow", [])
    if not shadow_items:
        return {}
    return shadow_items[0].get("reported", {}).get("properties", {})


# --------------------------------------------------------------------------- #
# Test runner state
# --------------------------------------------------------------------------- #

results: list[tuple[str, bool, str]] = []  # (label, passed, reason)


def run_test(label: str, fn):
    """Run a single test function, record result, print status line."""
    try:
        fn()
        passed = True
        reason = ""
    except AssertionError as e:
        passed = False
        reason = f"AssertionError: {e}"
    except Exception as e:
        passed = False
        reason = f"{type(e).__name__}: {e}"

    status = "PASS" if passed else f"FAIL: {reason}"
    # Pad label to 45 chars for alignment
    print(f"{label:<45} {status}")
    results.append((label, passed, reason))


# --------------------------------------------------------------------------- #
# Layer 1 — Direct tool calls
# --------------------------------------------------------------------------- #

def test_t1_toggle_light_bedroom_on():
    result = toggle_light.invoke({"room": "卧室", "on": True, "brightness": 80, "color": "白色"})
    assert "卧室灯已打开" in result, f"Got: {result!r}"


def test_t2_toggle_light_living_off():
    result = toggle_light.invoke({"room": "客厅", "on": False})
    assert "客厅灯已关闭" in result, f"Got: {result!r}"


def test_t3_set_temperature_bedroom():
    result = set_temperature.invoke({"room": "卧室", "value": 22})
    assert "卧室空调已设置为 22°C" in result, f"Got: {result!r}"


def test_t4_control_curtain_bedroom_open():
    result = control_curtain.invoke({"room": "卧室", "action": "open"})
    assert "卧室窗帘已打开" in result, f"Got: {result!r}"


def test_t5_start_robot_vacuum():
    result = start_robot_vacuum.invoke({"room": ""})
    assert "扫地机器人已启动" in result, f"Got: {result!r}"


# --------------------------------------------------------------------------- #
# Layer 2 — Full agent graph (async)
# --------------------------------------------------------------------------- #

async def _invoke_graph(user_input: str) -> AgentState:
    state = _make_state(user_input)
    return await graph.ainvoke(state)


def test_t6_graph_bedroom_light_on():
    result = asyncio.run(_invoke_graph("把卧室灯打开"))
    intent = result.get("current_intent", "")
    response = result.get("final_response", "")
    assert intent == "device_control", f"Expected intent=device_control, got: {intent!r}"
    assert response.strip(), "final_response is empty"


def test_t7_graph_bedroom_ac_24():
    result = asyncio.run(_invoke_graph("卧室空调调到24度"))
    intent = result.get("current_intent", "")
    response = result.get("final_response", "")
    assert intent == "device_control", f"Expected intent=device_control, got: {intent!r}"
    assert response.strip(), "final_response is empty"


def test_t8_graph_bedroom_curtain_close():
    result = asyncio.run(_invoke_graph("关上卧室窗帘"))
    intent = result.get("current_intent", "")
    response = result.get("final_response", "")
    assert intent == "device_control", f"Expected intent=device_control, got: {intent!r}"
    assert response.strip(), "final_response is empty"


# --------------------------------------------------------------------------- #
# Layer 3 — Shadow verification (read IoTDA shadow after Layer 1)
# --------------------------------------------------------------------------- #

def test_t9_shadow_bedroom_light_on():
    registry = _get_registry()
    device_id = registry.lookup("卧室", "light")["device_id"]
    props = _get_shadow_properties(device_id)
    assert props.get("on") is True, f"Expected on=True in shadow, got properties: {props}"


def test_t10_shadow_bedroom_ac_temperature():
    registry = _get_registry()
    device_id = registry.lookup("卧室", "ac")["device_id"]
    props = _get_shadow_properties(device_id)
    temp = props.get("temperature")
    assert temp == 22, f"Expected temperature=22 in shadow, got properties: {props}"


def test_t11_shadow_bedroom_curtain_open():
    registry = _get_registry()
    device_id = registry.lookup("卧室", "curtain")["device_id"]
    props = _get_shadow_properties(device_id)
    position = props.get("position")
    assert position == "open", f"Expected position='open' in shadow, got properties: {props}"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    print("=" * 60)
    print("IoTDA E2E Smoke Test — 11 cases across 3 layers")
    print("=" * 60)

    # Layer 1
    print("\n--- Layer 1: Direct tool calls ---")
    run_test("[T1]  toggle_light 卧室 ON", test_t1_toggle_light_bedroom_on)
    run_test("[T2]  toggle_light 客厅 OFF", test_t2_toggle_light_living_off)
    run_test("[T3]  set_temperature 卧室 22°C", test_t3_set_temperature_bedroom)
    run_test("[T4]  control_curtain 卧室 open", test_t4_control_curtain_bedroom_open)
    run_test("[T5]  start_robot_vacuum 全屋", test_t5_start_robot_vacuum)

    # Layer 2
    print("\n--- Layer 2: Full agent graph ---")
    run_test("[T6]  graph: 把卧室灯打开", test_t6_graph_bedroom_light_on)
    run_test("[T7]  graph: 卧室空调调到24度", test_t7_graph_bedroom_ac_24)
    run_test("[T8]  graph: 关上卧室窗帘", test_t8_graph_bedroom_curtain_close)

    # Layer 3
    print("\n--- Layer 3: Shadow verification ---")
    run_test("[T9]  shadow: 卧室 light → on=True", test_t9_shadow_bedroom_light_on)
    run_test("[T10] shadow: 卧室 AC → temperature=22", test_t10_shadow_bedroom_ac_temperature)
    run_test("[T11] shadow: 卧室 curtain → position=open", test_t11_shadow_bedroom_curtain_open)

    print("=" * 60)
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed

    if failed == 0:
        print(f"{passed}/{total} passed ✓")
        sys.exit(0)
    else:
        print(f"{passed}/{total} passed — {failed} failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
