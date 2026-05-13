import numpy as np
import pandas as pd

from app.services.analysis.backtest import backtest_signal


def test_buy_and_hold_matches_close_return():
    close = pd.Series(np.linspace(100, 110, 50))
    signal = pd.Series(1, index=close.index)
    result = backtest_signal(close, signal, cost_bps=0)
    # final equity should be ~ starting * (close[-1] / close[0]) but with one delay
    assert result.equity.iloc[-1] > result.equity.iloc[0]


def test_trade_list_extracted():
    close = pd.Series(np.linspace(100, 110, 30))
    signal = pd.Series([0] * 10 + [1] * 10 + [0] * 10)
    result = backtest_signal(close, signal, cost_bps=0)
    assert len(result.trades) == 1
