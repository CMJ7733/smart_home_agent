def test_chat_module_importable():
    import app.ui.pages.chat  # noqa: F401

def test_render_function_exists():
    from app.ui.pages.chat import render
    import inspect
    assert callable(render)
    assert len(inspect.signature(render).parameters) == 0
