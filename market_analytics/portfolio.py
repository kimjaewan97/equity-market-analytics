"""A monthly-rebalanced equal-weight book of the single names."""

from __future__ import annotations

import numpy as np
import pandas as pd


def monthly_equal_weight_returns(prices: pd.DataFrame) -> pd.Series:
    """Gross daily returns of an equal-weight book, reset on the first session of each month.

    Weights drift with each day's return and are set back to 1/N at the first
    trading day of the next month, before that day's return is earned.
    Transaction costs and dividends beyond the adjusted close are ignored.
    """
    px = prices.astype(float).dropna(how="any").sort_index()
    if px.shape[1] == 0 or len(px) < 2:
        return pd.Series(dtype=float)

    rets = px.pct_change()
    n = px.shape[1]
    weights = np.repeat(1.0 / n, n)
    previous_month = None
    out: dict[pd.Timestamp, float] = {}

    for i in range(1, len(px.index)):
        day = px.index[i]
        month = day.to_period("M")
        if previous_month is None or month != previous_month:
            weights = np.repeat(1.0 / n, n)
        day_ret = rets.iloc[i].to_numpy(dtype=float)
        out[day] = float(np.dot(weights, day_ret))
        weights = weights * (1.0 + day_ret)
        total = weights.sum()
        if total <= 0:
            weights = np.repeat(1.0 / n, n)
        else:
            weights = weights / total
        previous_month = month

    return pd.Series(out, name="equal_weight")


def wealth_index(returns: pd.Series, start: float = 100.0) -> pd.Series:
    r = returns.dropna()
    return start * (1.0 + r).cumprod()
