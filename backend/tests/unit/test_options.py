"""Unit tests for the Alpaca options service wrapper.

The tests stub the underlying alpaca-py client via monkeypatch so we never
touch the network. They assert call-shape, not real data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pandas as pd
import pytest

from app.services.alpaca import options as opt_mod


def test_module_exports_callables():
    assert callable(opt_mod.get_option_chain)
    assert callable(opt_mod.get_option_bars)
    assert callable(opt_mod.get_option_latest_quote)
    assert callable(opt_mod.get_option_latest_trade)


def test_no_trading_imports():
    """CI guard: options.py must not pull in alpaca.trading anywhere."""
    import inspect

    src = inspect.getsource(opt_mod)
    assert "alpaca.trading" not in src
    assert "TradingClient" not in src


@pytest.mark.asyncio
async def test_get_option_chain_call_shape(monkeypatch):
    """get_option_chain should build an OptionChainRequest and return JSON-ready dicts."""
    captured = {}

    fake_snapshot = SimpleNamespace(
        symbol="AAPL250620C00150000",
        latest_trade=SimpleNamespace(
            price=1.23, size=2, timestamp=datetime(2025, 5, 1, tzinfo=timezone.utc)
        ),
        latest_quote=SimpleNamespace(
            ask_price=1.30,
            ask_size=10,
            bid_price=1.20,
            bid_size=5,
            timestamp=datetime(2025, 5, 1, tzinfo=timezone.utc),
        ),
        implied_volatility=0.42,
        greeks=SimpleNamespace(delta=0.5, gamma=0.01, rho=0.0, theta=-0.02, vega=0.1),
    )

    class _FakeClient:
        def get_option_chain(self, req):
            captured["req"] = req
            return {fake_snapshot.symbol: fake_snapshot}

    opt_mod.get_client.cache_clear()
    monkeypatch.setattr(opt_mod, "get_client", lambda: _FakeClient())

    out = await opt_mod.get_option_chain("AAPL", expiration_date="2025-06-20")
    assert "AAPL250620C00150000" in out
    entry = out["AAPL250620C00150000"]
    assert entry["implied_volatility"] == 0.42
    assert entry["greeks"]["delta"] == 0.5
    assert entry["latest_quote"]["ask_price"] == 1.30
    # Request was built with the supplied underlying + parsed date.
    assert captured["req"].underlying_symbol == "AAPL"
    assert str(captured["req"].expiration_date) == "2025-06-20"


@pytest.mark.asyncio
async def test_get_option_bars_returns_dataframe(monkeypatch):
    """The wrapper should flatten the multi-index and return a DataFrame."""
    idx = pd.MultiIndex.from_tuples(
        [("AAPL250620C00150000", pd.Timestamp("2025-05-01", tz="UTC"))],
        names=["symbol", "timestamp"],
    )
    df = pd.DataFrame(
        {"open": [1.0], "high": [1.5], "low": [0.9], "close": [1.2], "volume": [100]},
        index=idx,
    )
    fake_bars = SimpleNamespace(df=df)

    class _FakeClient:
        def get_option_bars(self, req):
            return fake_bars

    opt_mod.get_client.cache_clear()
    monkeypatch.setattr(opt_mod, "get_client", lambda: _FakeClient())

    out = await opt_mod.get_option_bars("AAPL250620C00150000", timeframe="1Day", lookback="7d")
    assert isinstance(out, pd.DataFrame)
    assert not out.empty
    assert list(out.columns) == ["open", "high", "low", "close", "volume"]
