# Prompt 06 — Indicators, statistics, screeners, backtester

## Goal
A pure-functions analysis layer on top of pandas. No I/O. Inputs are DataFrames, outputs are DataFrames or scalars.

## Tasks
1. `backend/app/services/analysis/indicators.py`
   - Thin wrappers around `pandas_ta`:
     - `sma(close, length)`, `ema(close, length)`, `rsi(close, length=14)`, `macd(close, fast=12, slow=26, signal=9)`, `bbands(close, length=20, std=2)`, `atr(high, low, close, length=14)`, `vwap(high, low, close, volume)`, `obv(close, volume)`, `stoch(high, low, close)`.
   - Convenience: `compute(df: pd.DataFrame, indicators: list[str], params: dict) -> pd.DataFrame` returns the input frame plus added indicator columns.

2. `backend/app/services/analysis/stats.py`
   - `returns(close, periods=1, log=True)`
   - `sharpe(returns, rf=0.0, periods_per_year=252)`
   - `sortino(returns, rf=0.0, periods_per_year=252)`
   - `max_drawdown(equity_curve)` → tuple `(dd, peak_idx, trough_idx, recovery_idx)`
   - `calmar(returns, periods_per_year=252)`
   - `rolling_vol(returns, window=21, annualize=True)`
   - `beta(asset_returns, benchmark_returns)`
   - `correlation_matrix(returns_df)`

3. `backend/app/services/analysis/screeners.py`
   - `momentum(universe_df: dict[str, pd.DataFrame], lookback=63) -> list[tuple[str, float]]` ranked.
   - `mean_reversion(...)` — z-score against 20-day mean.
   - `breakout(...)` — 52-week high proximity + volume surge.

4. `backend/app/services/analysis/backtest.py`
   - Vectorized long-only signal backtester. Inputs: `close: pd.Series`, `signal: pd.Series` (boolean or {-1,0,1}). Returns `BacktestResult` with equity curve, trade list, perf summary.

5. Tests
   - `backend/tests/unit/test_indicators.py` — fixtures from synthetic price series (constant trend → SMA = price, sine wave → RSI ranges expected).
   - `backend/tests/unit/test_stats.py` — Sharpe of zero-mean noise ≈ 0; max-drawdown known.
   - `backend/tests/unit/test_backtest.py` — buy-and-hold sanity check.

## Constraints
- Zero I/O in this layer. Tests don't hit Alpaca.
- Pure functions; no globals; no caches.

## Acceptance
- `uv run pytest backend/tests/unit/test_indicators.py backend/tests/unit/test_stats.py backend/tests/unit/test_backtest.py` green.
