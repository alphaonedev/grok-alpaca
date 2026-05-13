import numpy as np
import pandas as pd

from app.services.analysis.stats import max_drawdown, sharpe, summary


def test_sharpe_of_zero_mean_noise_is_small():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0, 0.01, 5000))
    assert abs(sharpe(r)) < 0.5


def test_max_drawdown_known():
    equity = pd.Series([100, 120, 90, 110, 80, 130])
    dd = max_drawdown(equity)
    # peak 120 -> trough 80 = -33.3%
    assert dd["max_drawdown"] < -0.30


def test_summary_keys():
    r = pd.Series(np.linspace(-0.01, 0.01, 50))
    out = summary(r)
    for k in ("total_return", "cagr", "sharpe", "sortino", "calmar", "annualized_vol", "max_drawdown"):
        assert k in out
