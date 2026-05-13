"""Performance statistics — pure functions, no I/O."""

from __future__ import annotations

import numpy as np
import pandas as pd


def returns(close: pd.Series, periods: int = 1, log: bool = True) -> pd.Series:
    if log:
        return np.log(close / close.shift(periods)).dropna()
    return close.pct_change(periods).dropna()


def sharpe(r: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    excess = r - rf / periods_per_year
    sd = excess.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return 0.0
    return float((excess.mean() / sd) * np.sqrt(periods_per_year))


def sortino(r: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    excess = r - rf / periods_per_year
    downside = excess[excess < 0]
    sd = downside.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return 0.0
    return float((excess.mean() / sd) * np.sqrt(periods_per_year))


def max_drawdown(equity: pd.Series) -> dict:
    cummax = equity.cummax()
    dd = (equity - cummax) / cummax
    trough_idx = dd.idxmin() if not dd.empty else None
    peak_idx = equity.loc[:trough_idx].idxmax() if trough_idx is not None else None
    recovery_idx = None
    if peak_idx is not None and trough_idx is not None:
        recovery = equity.loc[trough_idx:]
        peak_val = equity.loc[peak_idx]
        above = recovery[recovery >= peak_val]
        recovery_idx = above.index[0] if not above.empty else None
    return {
        "max_drawdown": float(dd.min()) if not dd.empty else 0.0,
        "peak": peak_idx.isoformat() if hasattr(peak_idx, "isoformat") else peak_idx,
        "trough": trough_idx.isoformat() if hasattr(trough_idx, "isoformat") else trough_idx,
        "recovery": recovery_idx.isoformat() if hasattr(recovery_idx, "isoformat") else recovery_idx,
    }


def calmar(r: pd.Series, periods_per_year: int = 252) -> float:
    equity = (1 + r).cumprod()
    dd = max_drawdown(equity)["max_drawdown"]
    if dd == 0:
        return 0.0
    cagr = float(equity.iloc[-1] ** (periods_per_year / len(r)) - 1)
    return cagr / abs(dd)


def rolling_vol(r: pd.Series, window: int = 21, annualize: bool = True, periods_per_year: int = 252) -> pd.Series:
    sd = r.rolling(window).std(ddof=0)
    return sd * np.sqrt(periods_per_year) if annualize else sd


def beta(asset: pd.Series, benchmark: pd.Series) -> float:
    df = pd.concat([asset, benchmark], axis=1).dropna()
    if df.empty:
        return 0.0
    cov = df.cov().iloc[0, 1]
    var = df.iloc[:, 1].var(ddof=0)
    return float(cov / var) if var else 0.0


def summary(r: pd.Series, benchmark: pd.Series | None = None, periods_per_year: int = 252) -> dict:
    equity = (1 + r).cumprod()
    dd = max_drawdown(equity)
    out = {
        "total_return": float(equity.iloc[-1] - 1) if not equity.empty else 0.0,
        "cagr": float(equity.iloc[-1] ** (periods_per_year / max(len(r), 1)) - 1) if not equity.empty else 0.0,
        "sharpe": sharpe(r, periods_per_year=periods_per_year),
        "sortino": sortino(r, periods_per_year=periods_per_year),
        "calmar": calmar(r, periods_per_year=periods_per_year),
        "annualized_vol": float(r.std(ddof=0) * np.sqrt(periods_per_year)) if not r.empty else 0.0,
        "max_drawdown": dd["max_drawdown"],
    }
    if benchmark is not None and not benchmark.empty:
        out["beta"] = beta(r, benchmark)
    return out
