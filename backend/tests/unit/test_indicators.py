import numpy as np
import pandas as pd

from app.services.analysis.indicators import compute, ema, rsi, sma


def _trend_series(n=100, slope=1.0):
    return pd.Series(np.arange(n, dtype=float) * slope + 10.0)


def test_sma_constant_series_equals_value():
    s = pd.Series([5.0] * 50)
    out = sma(s, 10).dropna()
    assert (out == 5.0).all()


def test_ema_responds_to_step():
    s = pd.Series([1.0] * 20 + [10.0] * 20)
    e = ema(s, 5)
    assert e.iloc[-1] > e.iloc[20] > e.iloc[15]


def test_rsi_in_range():
    s = _trend_series()
    r = rsi(s, 14).dropna()
    assert (r >= 0).all() and (r <= 100).all()


def test_compute_adds_columns():
    df = pd.DataFrame({"open": _trend_series(), "high": _trend_series(slope=1.05), "low": _trend_series(slope=0.95), "close": _trend_series(), "volume": np.full(100, 1000.0)})
    out = compute(df, ["SMA", "EMA", "RSI", "MACD", "BBANDS"])
    assert "SMA_20" in out.columns
    assert "EMA_20" in out.columns
    assert "RSI_14" in out.columns
    assert any(c.startswith("MACD_") for c in out.columns)
    assert any(c.startswith("BBM_") for c in out.columns)
