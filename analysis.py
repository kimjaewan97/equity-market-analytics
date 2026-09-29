"""Run the equity case study end to end.

Usage (from this directory):
    python analysis.py            # use data/prices.csv if present, else download
    python analysis.py --refresh  # re-download adjusted closes from Yahoo Finance
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from market_analytics.download import download_panel  # noqa: E402
from market_analytics.metrics import performance_table, simple_returns  # noqa: E402
from market_analytics.plots import (  # noqa: E402
    plot_correlation,
    plot_drawdowns,
    plot_monthly_heatmap,
    plot_risk_return,
    plot_rolling_vol,
    plot_wealth,
)
from market_analytics.portfolio import monthly_equal_weight_returns, wealth_index  # noqa: E402
from market_analytics.universe import BENCHMARK, END, NAMES, PORTFOLIO_TICKERS, START  # noqa: E402

DATA = ROOT / "data" / "prices.csv"
FIGURES = ROOT / "figures"
RESULTS = ROOT / "results"
RF = 0.04


def load_prices(refresh: bool) -> pd.DataFrame:
    if DATA.exists() and not refresh:
        prices = pd.read_csv(DATA, index_col="date", parse_dates=True)
    else:
        prices = download_panel()
        DATA.parent.mkdir(parents=True, exist_ok=True)
        prices.to_csv(DATA, float_format="%.6f")
    prices = prices.sort_index()
    prices.index = pd.to_datetime(prices.index)
    return prices


def build_summary(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    book = prices[list(PORTFOLIO_TICKERS)]
    ew_returns = monthly_equal_weight_returns(book)
    ex_nvda = [ticker for ticker in PORTFOLIO_TICKERS if ticker != "NVDA"]
    ew_ex_returns = monthly_equal_weight_returns(prices[ex_nvda])
    panel = prices.copy()
    summary = performance_table(panel, BENCHMARK, RF)

    extras = pd.DataFrame(
        {
            "Equal weight": wealth_index(ew_returns),
            "Equal weight ex-NVDA": wealth_index(ew_ex_returns),
            BENCHMARK: prices[BENCHMARK],
        }
    )
    extra_stats = performance_table(extras.dropna(how="any"), BENCHMARK, RF)
    extra_stats = extra_stats.drop(index=BENCHMARK)
    summary = pd.concat([summary, extra_stats])
    return summary, ew_returns, ew_ex_returns


def write_summary(prices: pd.DataFrame, summary: pd.DataFrame, ew_returns: pd.Series, ew_ex_returns: pd.Series) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    pretty = summary.copy()
    for col in ("ann_return", "ann_volatility", "max_drawdown", "alpha_vs_spy", "total_return"):
        pretty[col] = (pretty[col] * 100).round(2)
    pretty["sharpe"] = pretty["sharpe"].round(2)
    pretty["beta_vs_spy"] = pretty["beta_vs_spy"].round(2)
    pretty.to_csv(RESULTS / "performance_summary.csv")

    lines = [
        "| Name | Ann. return | Ann. vol | Sharpe | Max DD | Beta | Alpha |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    order = list(PORTFOLIO_TICKERS) + [BENCHMARK, "Equal weight", "Equal weight ex-NVDA"]
    for ticker in order:
        row = pretty.loc[ticker]
        beta = "—" if pd.isna(row["beta_vs_spy"]) else f"{row['beta_vs_spy']:.2f}"
        alpha = "—" if pd.isna(row["alpha_vs_spy"]) else f"{row['alpha_vs_spy']:.1f}%"
        label = {
            "Equal weight": "Equal-weight book",
            "Equal weight ex-NVDA": "Equal-weight book, ex-NVIDIA",
        }.get(ticker, NAMES.get(ticker, ticker))
        lines.append(
            f"| {label} | {row['ann_return']:.1f}% | {row['ann_volatility']:.1f}% | "
            f"{row['sharpe']:.2f} | {row['max_drawdown']:.1f}% | {beta} | {alpha} |"
        )
    (RESULTS / "performance_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    ew = pretty.loc["Equal weight"]
    spy = pretty.loc[BENCHMARK]
    best = pretty.loc[list(PORTFOLIO_TICKERS), "ann_return"].idxmax()
    worst_dd = pretty.loc[list(PORTFOLIO_TICKERS), "max_drawdown"].idxmin()
    payload = {
        "start": str(prices.index.min().date()),
        "end": str(prices.index.max().date()),
        "sessions": int(prices.dropna(how="any").shape[0]),
        "risk_free": RF,
        "equal_weight_ann_return": float(summary.loc["Equal weight", "ann_return"]),
        "spy_ann_return": float(summary.loc[BENCHMARK, "ann_return"]),
        "equal_weight_sharpe": float(summary.loc["Equal weight", "sharpe"]),
        "spy_sharpe": float(summary.loc[BENCHMARK, "sharpe"]),
        "equal_weight_max_dd": float(summary.loc["Equal weight", "max_drawdown"]),
        "spy_max_dd": float(summary.loc[BENCHMARK, "max_drawdown"]),
        "best_name": best,
        "best_ann_return": float(summary.loc[best, "ann_return"]),
        "deepest_drawdown_name": worst_dd,
        "deepest_drawdown": float(summary.loc[worst_dd, "max_drawdown"]),
        "ex_nvda_ann_return": float(summary.loc["Equal weight ex-NVDA", "ann_return"]),
        "ex_nvda_sharpe": float(summary.loc["Equal weight ex-NVDA", "sharpe"]),
        "table_markdown": "\n".join(lines),
    }
    (RESULTS / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    findings = f"""# Measured results

Sample: {payload['start']} to {payload['end']} ({payload['sessions']} shared sessions).
Returns are price returns on Yahoo Finance adjusted closes, in USD.
Sharpe uses a constant {RF:.0%} risk-free rate. The equal-weight book is
rebalanced on the first session of each month and is gross of costs.

{payload['table_markdown']}

Reading the table:

* The equal-weight book annualized {ew['ann_return']:.1f}% versus {spy['ann_return']:.1f}% for SPY, with a Sharpe of {ew['sharpe']:.2f} versus {spy['sharpe']:.2f}.
* Dropping NVIDIA cuts the equal-weight annualized return to {pretty.loc['Equal weight ex-NVDA', 'ann_return']:.1f}% (Sharpe {pretty.loc['Equal weight ex-NVDA', 'sharpe']:.2f}). The outperformance is not a broad, balanced result.
* {NAMES[best]} was the strongest single name at {pretty.loc[best, 'ann_return']:.1f}% annualized.
* The deepest single-name drawdown was {NAMES[worst_dd]} at {pretty.loc[worst_dd, 'max_drawdown']:.1f}%.
* Beta and alpha are from a daily excess-return regression on SPY. Alpha is annualized and is not a claim of skill after costs or taxes.
"""
    (RESULTS / "FINDINGS.md").write_text(findings, encoding="utf-8")
    _ = (ew_returns, ew_ex_returns)


def main() -> None:
    parser = argparse.ArgumentParser(description="Equity market visual case study")
    parser.add_argument("--refresh", action="store_true", help="Re-download prices from Yahoo Finance")
    args = parser.parse_args()

    prices = load_prices(args.refresh)
    summary, ew_returns, ew_ex_returns = build_summary(prices)

    wealth_parts = {}
    for ticker in list(PORTFOLIO_TICKERS) + [BENCHMARK]:
        series = prices[ticker].dropna()
        wealth_parts[ticker] = 100.0 * series / series.iloc[0]
    wealth_parts["Equal weight"] = wealth_index(ew_returns)
    wealth_parts["Equal weight ex-NVDA"] = wealth_index(ew_ex_returns)
    wealth = pd.DataFrame(wealth_parts).dropna(how="all")

    plot_wealth(
        wealth[["Equal weight", "Equal weight ex-NVDA", BENCHMARK, "NVDA", "NVO"]],
        FIGURES / "growth_of_100.svg",
        log_scale=True,
    )
    focus = prices[["NVDA", "NVO", "JPM", BENCHMARK]]
    plot_drawdowns(focus, FIGURES / "drawdowns.svg")
    plot_rolling_vol(prices[["NVDA", "SHEL", "JPM", "SAP", BENCHMARK]], FIGURES / "rolling_volatility.svg")
    plot_correlation(prices, FIGURES / "correlation.svg")
    plot_risk_return(summary.drop(index="Equal weight"), FIGURES / "risk_return.svg")
    plot_monthly_heatmap(
        wealth_index(ew_returns),
        FIGURES / "monthly_equal_weight.svg",
        "Equal-weight book — calendar-month return (%)",
    )
    plot_monthly_heatmap(
        prices[BENCHMARK].dropna(),
        FIGURES / "monthly_spy.svg",
        "SPY — calendar-month return (%)",
    )
    write_summary(prices, summary, ew_returns, ew_ex_returns)
    print(f"Sample {prices.index.min().date()} → {prices.index.max().date()} ({len(prices)} rows)")
    print((RESULTS / "performance_table.md").read_text())


if __name__ == "__main__":
    main()
