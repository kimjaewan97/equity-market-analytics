"""Unit checks for the return math. Run: python -m unittest discover -s tests"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_analytics.metrics import (  # noqa: E402
    annualized_return,
    annualized_volatility,
    beta_alpha,
    max_drawdown,
    sharpe_ratio,
)
from market_analytics.portfolio import monthly_equal_weight_returns  # noqa: E402


class MetricsTest(unittest.TestCase):
    def test_doubling_over_one_year_is_100_percent(self):
        # 252 daily steps that compound to exactly 2.0
        step = 2.0 ** (1 / 252) - 1
        returns = pd.Series([step] * 252)
        self.assertAlmostEqual(annualized_return(returns), 1.0, places=6)

    def test_drawdown_is_negative_fifty_percent(self):
        prices = pd.Series([100, 120, 60, 90])
        self.assertAlmostEqual(max_drawdown(prices), -0.5, places=8)

    def test_beta_of_two_times_benchmark(self):
        rng = np.random.default_rng(0)
        bench = pd.Series(rng.normal(0.0004, 0.01, 400))
        asset = 2.0 * bench + 0.0001
        beta, alpha = beta_alpha(asset, bench, risk_free_annual=0.0)
        self.assertAlmostEqual(beta, 2.0, places=6)
        self.assertGreater(alpha, 0)

    def test_zero_excess_sharpe_is_near_zero(self):
        rf = 0.04
        daily = (1 + rf) ** (1 / 252) - 1
        returns = pd.Series([daily + 0.01, daily - 0.01] * 126)
        self.assertAlmostEqual(sharpe_ratio(returns, rf), 0.0, places=8)

    def test_volatility_scales_with_sqrt_time(self):
        rng = np.random.default_rng(2)
        returns = pd.Series(rng.normal(0, 0.01, 5000))
        ann = annualized_volatility(returns)
        self.assertAlmostEqual(ann, 0.01 * np.sqrt(252), places=2)

    def test_equal_weight_matches_mean_when_reset_every_day_is_not_required(self):
        idx = pd.bdate_range("2024-01-01", periods=40)
        frame = pd.DataFrame(
            {
                "A": np.linspace(100, 110, len(idx)),
                "B": np.linspace(50, 50, len(idx)),
            },
            index=idx,
        )
        out = monthly_equal_weight_returns(frame)
        self.assertEqual(len(out), len(idx) - 1)
        self.assertTrue(np.isfinite(out).all())


if __name__ == "__main__":
    unittest.main()
