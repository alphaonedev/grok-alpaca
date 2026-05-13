"""Technical indicators — thin wrappers over pandas_ta with safe fallbacks."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

try:
    import pandas_ta as ta  # noqa: F401

    _HAVE_TA = True
except Exception:
    _HAVE_TA = False


def _ensure_close(df: pd.DataFrame) -> pd.Series:
    if "close" not in df.columns:
        raise ValueError("DataFrame must have a 'close' column")
    return df["close"].astype(float)


def sma(close: pd.Series, length: int = 20) -> pd.Series:
    return close.rolling(length).mean().rename(f"SMA_{length}")


def ema(close: pd.Series, length: int = 20) -> pd.Series:
    return close.ewm(span=length, adjust=False).mean().rename(f"EMA_{length}")


def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).rename(f"RSI_{length}")


def macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    fast_ema = close.ewm(span=fast, adjust=False).mean()
    slow_ema = close.ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    sig_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - sig_line
    return pd.DataFrame(
        {
            f"MACD_{fast}_{slow}_{signal}": macd_line,
            f"MACDs_{fast}_{slow}_{signal}": sig_line,
            f"MACDh_{fast}_{slow}_{signal}": hist,
        }
    )


def bbands(close: pd.Series, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    mid = close.rolling(length).mean()
    sd = close.rolling(length).std(ddof=0)
    upper = mid + std * sd
    lower = mid - std * sd
    return pd.DataFrame(
        {
            f"BBL_{length}_{std}": lower,
            f"BBM_{length}_{std}": mid,
            f"BBU_{length}_{std}": upper,
        }
    )


def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False).mean().rename(f"ATR_{length}")


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    typical = (high + low + close) / 3
    cum_pv = (typical * volume).cumsum()
    cum_v = volume.cumsum().replace(0, np.nan)
    return (cum_pv / cum_v).rename("VWAP")


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).cumsum().rename("OBV")


def stoch(
    high: pd.Series, low: pd.Series, close: pd.Series, k: int = 14, d: int = 3
) -> pd.DataFrame:
    ll = low.rolling(k).min()
    hh = high.rolling(k).max()
    fast_k = 100 * (close - ll) / (hh - ll).replace(0, np.nan)
    slow_d = fast_k.rolling(d).mean()
    return pd.DataFrame({f"STOCHk_{k}_{d}": fast_k, f"STOCHd_{k}_{d}": slow_d})


def compute(df: pd.DataFrame, indicators: list[str], params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Return df with the requested indicator columns appended."""
    params = params or {}
    out = df.copy()
    close = _ensure_close(out)
    high = out["high"].astype(float) if "high" in out else close
    low = out["low"].astype(float) if "low" in out else close
    volume = out["volume"].astype(float) if "volume" in out else pd.Series(0, index=close.index)

    for name in indicators:
        key = name.upper()
        if key == "SMA":
            out = out.join(sma(close, params.get("sma_length", 20)))
        elif key == "EMA":
            out = out.join(ema(close, params.get("ema_length", 20)))
        elif key == "RSI":
            out = out.join(rsi(close, params.get("rsi_length", 14)))
        elif key == "MACD":
            out = out.join(macd(close, params.get("macd_fast", 12), params.get("macd_slow", 26), params.get("macd_signal", 9)))
        elif key == "BBANDS":
            out = out.join(bbands(close, params.get("bb_length", 20), params.get("bb_std", 2.0)))
        elif key == "ATR":
            out = out.join(atr(high, low, close, params.get("atr_length", 14)))
        elif key == "VWAP":
            out = out.join(vwap(high, low, close, volume))
        elif key == "OBV":
            out = out.join(obv(close, volume))
        elif key == "STOCH":
            out = out.join(stoch(high, low, close, params.get("stoch_k", 14), params.get("stoch_d", 3)))
        else:
            raise ValueError(f"unknown indicator {name!r}")
    return out
