def test_scenes_module_importable():
    import app.ui.pages.scenes  # noqa: F401

def test_render_exists():
    from app.ui.pages.scenes import render, SCENES
    import inspect
    assert callable(render)
    assert len(SCENES) == 3
    scene_names = [s["name"] for s in SCENES]
    assert "睡眠模式" in scene_names
    assert "离家模式" in scene_names
    assert "观影模式" in scene_names
