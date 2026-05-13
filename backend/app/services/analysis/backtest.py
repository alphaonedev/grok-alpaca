"""Tiny vectorized long-only signal backtester."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from app.services.analysis.stats import summary


@dataclass
class BacktestResult:
    equity: pd.Series
    returns: pd.Series
    trades: list[dict]
    perf: dict

    def to_dict(self) -> dict:
        return {
            "equity": [
                {"t": t.isoformat() if hasattr(t, "isoformat") else str(t), "v": float(v)}
                for t, v in self.equity.items()
            ],
            "trades": self.trades,
            "perf": self.perf,
        }


def backtest_signal(
    close: pd.Series,
    signal: pd.Series,
    starting_equity: float = 10_000.0,
    cost_bps: float = 5.0,
) -> BacktestResult:
    """Long-only vectorized backtest. `signal` is {0,1} or {-1,0,1}; we treat >0 as long, else flat."""
    close = close.astype(float)
    sig = signal.astype(float).clip(lower=0, upper=1).reindex(close.index).fillna(0)
    pos = sig.shift(1).fillna(0)
    rets = close.pct_change().fillna(0)
    strategy_rets = pos * rets

    # Apply trading costs on position changes.
    changes = pos.diff().abs().fillna(0)
    strategy_rets = strategy_rets - changes * (cost_bps / 1e4)

    equity = (1 + strategy_rets).cumprod() * starting_equity

    # Trade list — entries on 0→1, exits on 1→0.
    trades: list[dict] = []
    entry_t: pd.Timestamp | None = None
    entry_p: float | None = None
    for t, p in pos.items():
        prev = pos.shift(1).get(t, 0.0)
        if prev == 0 and p == 1:
            entry_t, entry_p = t, float(close.loc[t])
        elif prev == 1 and p == 0 and entry_t is not None:
            exit_p = float(close.loc[t])
            trades.append(
                {
                    "entry": entry_t.isoformat() if hasattr(entry_t, "isoformat") else str(entry_t),
                    "exit": t.isoformat() if hasattr(t, "isoformat") else str(t),
                    "entry_price": entry_p,
                    "exit_price": exit_p,
                    "return": exit_p / entry_p - 1 if entry_p else 0.0,
                }
            )
            entry_t, entry_p = None, None

    perf = summary(strategy_rets[strategy_rets != 0])
    return BacktestResult(equity=equity, returns=strategy_rets, trades=trades, perf=perf)
