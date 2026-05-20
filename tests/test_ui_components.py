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
