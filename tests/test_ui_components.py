import pytest

def test_imports():
    from app.ui.components import (
        header_bar, device_card, scene_card,
        metric_card, tool_call_card, status_badge,
    )

def test_status_badge_returns_html():
    from app.ui.components import status_badge
    online_html = status_badge(True)
    offline_html = status_badge(False)
    assert "在线" in online_html
    assert "离线" in offline_html
    assert "sh-badge-online" in online_html
    assert "sh-badge-offline" in offline_html


def test_tool_call_card_success(monkeypatch):
    import streamlit as st
    calls = []
    monkeypatch.setattr(st, "markdown", lambda html, **kw: calls.append(html))
    from app.ui.components import tool_call_card
    tool_call_card([{"success": True, "device": "卧室灯", "result": "已打开"}])
    assert calls
    assert "sh-tool-card" in calls[0]
    assert "✅" in calls[0]
    assert "sh-tool-result-ok" in calls[0]

def test_tool_call_card_failure(monkeypatch):
    import streamlit as st
    calls = []
    monkeypatch.setattr(st, "markdown", lambda html, **kw: calls.append(html))
    from app.ui.components import tool_call_card
    tool_call_card([{"success": False, "device": "空调", "result": "超时"}])
    assert "❌" in calls[0]
    assert "sh-tool-result-err" in calls[0]

def test_tool_call_card_empty_is_noop(monkeypatch):
    import streamlit as st
    calls = []
    monkeypatch.setattr(st, "markdown", lambda html, **kw: calls.append(html))
    from app.ui.components import tool_call_card
    tool_call_card([])
    assert calls == []

def test_device_card_active_state(monkeypatch):
    import streamlit as st
    calls = []
    monkeypatch.setattr(st, "markdown", lambda html, **kw: calls.append(html))
    from app.ui.components import device_card
    device_card("卧室灯", "💡", online=True, on=True, properties={})
    assert "sh-card-active" in calls[0]

def test_device_card_offline_state(monkeypatch):
    import streamlit as st
    calls = []
    monkeypatch.setattr(st, "markdown", lambda html, **kw: calls.append(html))
    from app.ui.components import device_card
    device_card("卧室灯", "💡", online=False, on=False, properties={})
    assert "#EF4444" in calls[0]
    assert "sh-card-active" not in calls[0]

def test_xss_escaping_in_tool_call_card(monkeypatch):
    import streamlit as st
    calls = []
    monkeypatch.setattr(st, "markdown", lambda html, **kw: calls.append(html))
    from app.ui.components import tool_call_card
    tool_call_card([{"device": '<script>alert(1)</script>', "result": "ok"}])
    assert "<script>" not in calls[0]
    assert "&lt;script&gt;" in calls[0]
