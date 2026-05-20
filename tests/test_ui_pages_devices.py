def test_devices_module_importable():
    import app.ui.pages.devices  # noqa: F401

def test_render_exists():
    from app.ui.pages.devices import render
    import inspect
    assert callable(render)
    assert len(inspect.signature(render).parameters) == 0

def test_device_type_to_icon_covers_known_types():
    from app.ui.pages.devices import DEVICE_ICONS
    for t in ("light", "ac", "curtain", "vacuum"):
        assert t in DEVICE_ICONS
