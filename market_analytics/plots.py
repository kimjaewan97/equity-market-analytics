"""Figures for the case study. Saved as SVG so the README can embed them."""

from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from market_analytics.metrics import drawdown_series, simple_returns
from market_analytics.universe import NAMES

PAPER = "#f4f1ea"
INK = "#1c1917"
MUTED = "#57534e"
GRID = "#e7e5e4"
UP = "#0f6e56"
DOWN = "#9f1239"
SPINE = "#d6d3d1"

SERIES = [
    "#0f6e56",
    "#1d4e89",
    "#b45309",
    "#7f1d1d",
    "#3f6212",
    "#0e7490",
    "#9a3412",
    "#334155",
    "#6b21a8",
    "#44403c",
]


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "axes.edgecolor": SPINE,
            "axes.titleweight": "semibold",
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "font.size": 10,
            "font.family": "DejaVu Sans",
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
        }
    )


def _finish(ax, title: str, ylabel: str | None = None) -> None:
    ax.set_title(title, loc="left", pad=12, color=INK)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.figure.autofmt_xdate(rotation=0, ha="center")


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, format="svg", bbox_inches="tight")
    fig.savefig(path.with_suffix(".png"), format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def plot_wealth(wealth: pd.DataFrame, path: Path, log_scale: bool = False) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.2))
    emphasis = {"Equal weight", "Equal weight ex-NVDA", "SPY"}
    for i, column in enumerate(wealth.columns):
        width = 2.3 if column in emphasis else 1.5
        ax.plot(
            wealth.index,
            wealth[column],
        label={"Equal weight ex-NVDA": "Equal weight ex-NVIDIA"}.get(column, NAMES.get(column, column)),
            color=SERIES[i % len(SERIES)],
            lw=width,
        )
    ax.axhline(100, color=MUTED, lw=0.6, zorder=0)
    if log_scale:
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: f"{value:.0f}"))
    _finish(ax, "Growth of 100 — adjusted close, USD" + (" (log scale)" if log_scale else ""), "Index")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    _save(fig, path)


def plot_drawdowns(prices: pd.DataFrame, path: Path) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(11, 5.4))
    for column in prices.columns:
        dd = drawdown_series(prices[column]) * 100
        ax.plot(dd.index, dd.values, label=NAMES.get(column, column), lw=1.4)
    _finish(ax, "Drawdown from the running peak", "Percent")
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    _save(fig, path)


def plot_rolling_vol(prices: pd.DataFrame, path: Path, window: int = 63) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(11, 5.4))
    for i, column in enumerate(prices.columns):
        vol = simple_returns(prices[column]).rolling(window).std() * np.sqrt(252) * 100
        ax.plot(vol.index, vol.values, label=NAMES.get(column, column), color=SERIES[i % len(SERIES)], lw=1.3)
    _finish(ax, f"{window}-session rolling volatility, annualized", "Percent")
    ax.legend(ncol=2, frameon=False, fontsize=8)
    _save(fig, path)


def plot_correlation(prices: pd.DataFrame, path: Path) -> None:
    _style()
    returns = prices.pct_change().dropna(how="any")
    corr = returns.corr()
    labels = [NAMES.get(c, c) for c in corr.columns]
    fig, ax = plt.subplots(figsize=(8.6, 7.2))
    cmap = LinearSegmentedColormap.from_list("risk", ["#9f1239", "#f4f1ea", "#0f6e56"])
    image = ax.imshow(corr.values, cmap=cmap, vmin=-1, vmax=1)
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.grid(False)
    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=8, color=INK)
    ax.set_title("Daily-return correlation", loc="left", pad=12)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    _save(fig, path)


def plot_risk_return(summary: pd.DataFrame, path: Path) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    ax.axhline(0, color=SPINE, lw=0.6)
    ax.scatter(
        summary["ann_volatility"] * 100,
        summary["ann_return"] * 100,
        s=70,
        color=UP,
        zorder=3,
    )
    for ticker, row in summary.iterrows():
        ax.annotate(
            NAMES.get(str(ticker), str(ticker)),
            (row["ann_volatility"] * 100, row["ann_return"] * 100),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=8,
            color=INK,
        )
    ax.set_xlabel("Annualized volatility (%)")
    ax.set_ylabel("Annualized return (%)")
    ax.set_title("Risk and return, full sample", loc="left", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=0)
    _save(fig, path)


def plot_monthly_heatmap(prices: pd.Series, path: Path, title: str) -> None:
    _style()
    monthly = prices.resample("ME").last().pct_change().dropna()
    frame = pd.DataFrame({"ret": monthly})
    frame["year"] = frame.index.year
    frame["month"] = frame.index.month
    pivot = frame.pivot(index="year", columns="month", values="ret") * 100
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    cmap = LinearSegmentedColormap.from_list("pnl", ["#9f1239", "#f4f1ea", "#0f6e56"])
    limit = np.nanmax(np.abs(pivot.values))
    image = ax.imshow(pivot.values, cmap=cmap, vmin=-limit, vmax=limit, aspect="auto")
    ax.set_xticks(range(12), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_yticks(range(len(pivot.index)), pivot.index.astype(str))
    ax.grid(False)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            value = pivot.values[i, j]
            if np.isnan(value):
                continue
            ax.text(j, i, f"{value:.1f}", ha="center", va="center", fontsize=7.5, color=INK)
    ax.set_title(title, loc="left", pad=12)
    fig.colorbar(image, ax=ax, fraction=0.02, pad=0.02)
    _save(fig, path)
