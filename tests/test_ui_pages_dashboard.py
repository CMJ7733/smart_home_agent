def test_dashboard_module_importable():
    import app.ui.pages.dashboard  # noqa: F401

def test_render_exists():
    from app.ui.pages.dashboard import render
    import inspect
    assert callable(render)

def test_build_intent_dist_returns_dict():
    from app.ui.pages.dashboard import _build_intent_dist
    logs = [
        {"intent": "device_control"},
        {"intent": "device_control"},
        {"intent": "kb_query"},
        {"intent": "chitchat"},
    ]
    result = _build_intent_dist(logs)
    assert result["device_control"] == 2
    assert result["kb_query"] == 1
    assert result["chitchat"] == 1
