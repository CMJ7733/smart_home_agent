from app.ui.styles import CSS, inject_css

def test_css_contains_key_tokens():
    assert "#F5F7FA" in CSS          # page background
    assert "#6366F1" in CSS          # primary color
    assert "Inter" in CSS            # font

def test_inject_css_returns_none(monkeypatch):
    import streamlit as st
    monkeypatch.setattr(st, "markdown", lambda *a, **kw: None)
    assert inject_css() is None
