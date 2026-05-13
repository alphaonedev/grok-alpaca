"""Simple screeners over a universe of (symbol -> DataFrame)."""

from __future__ import annotations

import pandas as pd

from app.services.analysis.indicators import bbands, rsi


def momentum(universe: dict[str, pd.DataFrame], lookback: int = 63) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for sym, df in universe.items():
        if "close" not in df or len(df) < lookback + 1:
            continue
        c = df["close"].astype(float)
        ret = float(c.iloc[-1] / c.iloc[-lookback - 1] - 1)
        out.append((sym, ret))
    return sorted(out, key=lambda kv: kv[1], reverse=True)


def mean_reversion(universe: dict[str, pd.DataFrame], length: int = 20) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for sym, df in universe.items():
        if "close" not in df or len(df) < length + 1:
            continue
        c = df["close"].astype(float)
        z = (c.iloc[-1] - c.rolling(length).mean().iloc[-1]) / (c.rolling(length).std(ddof=0).iloc[-1] or 1.0)
        out.append((sym, float(z)))
    return sorted(out, key=lambda kv: kv[1])  # most negative z first


def breakout(universe: dict[str, pd.DataFrame], window: int = 252) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for sym, df in universe.items():
        if "close" not in df or len(df) < window:
            continue
        c = df["close"].astype(float)
        proximity = float(c.iloc[-1] / c.rolling(window).max().iloc[-1])
        out.append((sym, proximity))
    return sorted(out, key=lambda kv: kv[1], reverse=True)


def overbought(universe: dict[str, pd.DataFrame], rsi_length: int = 14, threshold: float = 70.0) -> list[str]:
    return [sym for sym, df in universe.items() if "close" in df and not df.empty and rsi(df["close"].astype(float), rsi_length).iloc[-1] > threshold]


def oversold(universe: dict[str, pd.DataFrame], rsi_length: int = 14, threshold: float = 30.0) -> list[str]:
    return [sym for sym, df in universe.items() if "close" in df and not df.empty and rsi(df["close"].astype(float), rsi_length).iloc[-1] < threshold]
