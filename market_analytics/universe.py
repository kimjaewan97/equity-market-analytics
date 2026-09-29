"""Tradable universe. Every name is a USD listing so returns are comparable."""

# Yahoo Finance symbols. ADRs / USD listings are used for European issuers
# (ASML, SAP, SHEL, NVO) so the panel does not mix EUR and USD prices.
TICKERS = ("AAPL", "MSFT", "NVDA", "AMZN", "ASML", "SAP", "JPM", "SHEL", "NVO", "SPY")

NAMES = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "ASML": "ASML",
    "SAP": "SAP",
    "JPM": "JPMorgan Chase",
    "SHEL": "Shell",
    "NVO": "Novo Nordisk",
    "SPY": "S&P 500 ETF",
}

BENCHMARK = "SPY"

# Single-name book. SPY is the benchmark, not a portfolio constituent.
PORTFOLIO_TICKERS = tuple(t for t in TICKERS if t != BENCHMARK)

# Sample window. Adjusted closes are cached in data/prices.csv.
START = "2023-01-01"
END = "2026-09-26"
