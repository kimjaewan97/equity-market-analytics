"""Cache Yahoo Finance adjusted closes.

The chart endpoint is unauthenticated. Prices are stored so the rest of the
project runs with no network access.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import pandas as pd

from market_analytics.universe import END, START, TICKERS

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&period1={start}&period2={end}"


def _unix(day: str) -> int:
    dt = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def fetch_adjusted_close(symbol: str, start: str = START, end: str = END, retries: int = 3) -> pd.Series:
    url = YAHOO.format(symbol=symbol, start=_unix(start), end=_unix(end))
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 research-case-study"})
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode())
            result = payload["chart"]["result"][0]
            stamps = result["timestamp"]
            adjusted = result["indicators"]["adjclose"][0]["adjclose"]
            index = pd.to_datetime(stamps, unit="s", utc=True).tz_convert(None).normalize()
            series = pd.Series(adjusted, index=index, name=symbol, dtype="float64")
            return series.dropna().sort_index()
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to download {symbol}") from last_error


def download_panel(start: str = START, end: str = END) -> pd.DataFrame:
    frames = []
    for symbol in TICKERS:
        frames.append(fetch_adjusted_close(symbol, start, end))
        time.sleep(0.25)
    panel = pd.concat(frames, axis=1, join="inner").sort_index()
    panel.index.name = "date"
    return panel
