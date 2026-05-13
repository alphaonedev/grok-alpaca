import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("XAI_API_KEY", "test-xai")
os.environ.setdefault("ALPACA_API_KEY", "test-alpaca")
os.environ.setdefault("ALPACA_SECRET_KEY", "test-alpaca-secret")
os.environ.setdefault("DATA_DIR", "/tmp/grok-alpaca-tests")


@pytest.fixture(autouse=True)
def _clean_settings_cache():
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
