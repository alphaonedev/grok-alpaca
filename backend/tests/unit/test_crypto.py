"""Unit tests for the Alpaca crypto service wrapper."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pandas as pd
import pytest

from app.services.alpaca import crypto as crypto_mod


def test_module_exports_callables():
    assert callable(crypto_mod.get_crypto_bars)
    assert callable(crypto_mod.get_crypto_latest_quote)
    assert callable(crypto_mod.get_crypto_latest_trade)


def test_no_trading_imports():
    import inspect

    src = inspect.getsource(crypto_mod)
    assert "alpaca.trading" not in src
    assert "TradingClient" not in src


@pytest.mark.asyncio
async def test_get_crypto_bars_returns_expected_shape(monkeypatch):
    """Stub CryptoHistoricalDataClient.get_crypto_bars and assert wrapper shape."""
    idx = pd.MultiIndex.from_tuples(
        [
            ("BTC/USD", pd.Timestamp("2025-05-01", tz="UTC")),
            ("BTC/USD", pd.Timestamp("2025-05-02", tz="UTC")),
        ],
        names=["symbol", "timestamp"],
    )
    raw_df = pd.DataFrame(
        {
            "open": [60_000.0, 61_000.0],
            "high": [62_000.0, 63_000.0],
            "low": [59_000.0, 60_500.0],
            "close": [61_000.0, 62_500.0],
            "volume": [10.0, 12.0],
        },
        index=idx,
    )
    fake_bars = SimpleNamespace(df=raw_df)

    class _FakeClient:
        def get_crypto_bars(self, req):
            # Sanity: the wrapper should send the symbol we asked for.
            assert req.symbol_or_symbols == "BTC/USD"
            return fake_bars

    crypto_mod.get_client.cache_clear()
    monkeypatch.setattr(crypto_mod, "get_client", lambda: _FakeClient())

    df = await crypto_mod.get_crypto_bars("BTC/USD", timeframe="1Day", lookback="7d")
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 5)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    # Multi-index should have been flattened to just timestamps.
    assert not isinstance(df.index, pd.MultiIndex)


@pytest.mark.asyncio
async def test_get_crypto_latest_quote_returns_dict(monkeypatch):
    fake_quote = SimpleNamespace(
        ask_price=61_500.0,
        ask_size=0.5,
        bid_price=61_400.0,
        bid_size=0.6,
        timestamp=datetime(2025, 5, 13, tzinfo=timezone.utc),
    )

    class _FakeClient:
        def get_crypto_latest_quote(self, req):
            return {"BTC/USD": fake_quote}

    crypto_mod.get_client.cache_clear()
    monkeypatch.setattr(crypto_mod, "get_client", lambda: _FakeClient())

    out = await crypto_mod.get_crypto_latest_quote("BTC/USD")
    assert out["symbol"] == "BTC/USD"
    assert out["ask_price"] == 61_500.0
    assert out["bid_price"] == 61_400.0
    assert out["timestamp"].startswith("2025-05-13")
