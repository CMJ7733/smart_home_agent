import pytest

def test_eval_logs_module_importable():
    import app.ui.pages.eval_logs  # noqa: F401

def test_render_exists():
    from app.ui.pages.eval_logs import render
    import inspect
    assert callable(render)

def test_avg_score():
    from app.ui.pages.eval_logs import _avg_score
    assert _avg_score('{"faithfulness": 0.8, "answer_relevancy": 0.6}') == pytest.approx(0.7)
    assert _avg_score(None) is None
    assert _avg_score("") is None

def test_feedback_label():
    from app.ui.pages.eval_logs import _feedback_label
    assert _feedback_label(1) == "👍"
    assert _feedback_label(-1) == "👎"
    assert _feedback_label(None) == "-"
