import os

from app.core.config import Settings, get_settings


def test_defaults():
    s = Settings()
    assert s.host == "127.0.0.1"
    assert s.port == 8000
    assert s.alpaca_data_feed in ("iex", "sip")


def test_env_override(monkeypatch):
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("GROK_MODEL", "grok-test")
    get_settings.cache_clear()
    s = get_settings()
    assert s.port == 9000
    assert s.grok_model == "grok-test"
