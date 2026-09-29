"""Price-return statistics.

Conventions
-----------
* Inputs are adjusted close prices unless noted.
* Returns are simple daily returns, not log returns.
* Annualization uses 252 trading days.
* The Sharpe ratio uses a constant annual risk-free rate, converted to a
  daily compounded equivalent. Default is 4%, a round figure for 2023–2026
  US T-bill yields — not a traded bill series.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def simple_returns(prices: pd.Series) -> pd.Series:
    return prices.astype(float).pct_change()


def _clean(returns: pd.Series) -> pd.Series:
    return returns.replace([np.inf, -np.inf], np.nan).dropna()


def annualized_return(returns: pd.Series) -> float:
    r = _clean(returns)
    if r.empty:
        return np.nan
    growth = float((1.0 + r).prod())
    years = len(r) / TRADING_DAYS
    if years <= 0 or growth <= 0:
        return np.nan
    return growth ** (1.0 / years) - 1.0


def annualized_volatility(returns: pd.Series) -> float:
    r = _clean(returns)
    if len(r) < 2:
        return np.nan
    return float(r.std(ddof=1) * np.sqrt(TRADING_DAYS))


def sharpe_ratio(returns: pd.Series, risk_free_annual: float = 0.04) -> float:
    r = _clean(returns)
    if len(r) < 2:
        return np.nan
    rf_daily = (1.0 + risk_free_annual) ** (1.0 / TRADING_DAYS) - 1.0
    excess = r - rf_daily
    vol = float(excess.std(ddof=1))
    if vol == 0.0 or np.isnan(vol):
        return np.nan
    return float(excess.mean() / vol * np.sqrt(TRADING_DAYS))


def drawdown_series(prices: pd.Series) -> pd.Series:
    wealth = prices.astype(float).dropna()
    peak = wealth.cummax()
    return wealth / peak - 1.0


def max_drawdown(prices: pd.Series) -> float:
    dd = drawdown_series(prices)
    if dd.empty:
        return np.nan
    return float(dd.min())


def max_drawdown_window(prices: pd.Series) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Peak date and trough date of the worst peak-to-trough loss."""
    wealth = prices.astype(float).dropna()
    if wealth.empty:
        return None, None
    dd = drawdown_series(wealth)
    trough = dd.idxmin()
    peak = wealth.loc[:trough].idxmax()
    return peak, trough


def beta_alpha(
    asset_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_annual: float = 0.04,
) -> tuple[float, float]:
    """OLS beta and annualized alpha of excess returns on excess benchmark.

    Alpha is annualized with daily compounding: (1 + mean daily alpha)^252 - 1.
    """
    df = pd.concat(
        [asset_returns.rename("asset"), benchmark_returns.rename("bench")],
        axis=1,
        join="inner",
    )
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    if len(df) < 3:
        return np.nan, np.nan
    rf_daily = (1.0 + risk_free_annual) ** (1.0 / TRADING_DAYS) - 1.0
    y = df["asset"] - rf_daily
    x = df["bench"] - rf_daily
    var_x = float(np.var(x, ddof=1))
    if var_x == 0.0:
        return np.nan, np.nan
    beta = float(np.cov(y, x, ddof=1)[0, 1] / var_x)
    alpha_daily = float(y.mean() - beta * x.mean())
    alpha_annual = (1.0 + alpha_daily) ** TRADING_DAYS - 1.0
    return beta, float(alpha_annual)


def performance_table(
    prices: pd.DataFrame,
    benchmark: str,
    risk_free_annual: float = 0.04,
) -> pd.DataFrame:
    """One row per column in `prices`."""
    bench_ret = simple_returns(prices[benchmark])
    rows = []
    for ticker in prices.columns:
        px = prices[ticker]
        rets = simple_returns(px)
        beta, alpha = (np.nan, np.nan)
        if ticker != benchmark:
            beta, alpha = beta_alpha(rets, bench_ret, risk_free_annual)
        peak, trough = max_drawdown_window(px.dropna())
        rows.append(
            {
                "ticker": ticker,
                "ann_return": annualized_return(rets),
                "ann_volatility": annualized_volatility(rets),
                "sharpe": sharpe_ratio(rets, risk_free_annual),
                "max_drawdown": max_drawdown(px),
                "drawdown_peak": peak,
                "drawdown_trough": trough,
                "beta_vs_spy": beta,
                "alpha_vs_spy": alpha,
                "total_return": float(px.dropna().iloc[-1] / px.dropna().iloc[0] - 1.0),
            }
        )
    return pd.DataFrame(rows).set_index("ticker")
