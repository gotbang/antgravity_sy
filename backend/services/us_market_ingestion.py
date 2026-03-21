from __future__ import annotations

from typing import Any

import httpx
import yfinance as yf


def collect_us_universe() -> list[dict[str, Any]]:
    response = httpx.get("https://www.sec.gov/files/company_tickers.json", headers={"User-Agent": "AntGravity support@local.dev"}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    rows: list[dict[str, Any]] = []
    for item in payload.values():
        ticker = str(item.get("ticker", "")).strip()
        if not ticker:
            continue
        rows.append(
            {
                "symbol": ticker,
                "market": "US",
                "name": item.get("title"),
                "sector": None,
                "industry": None,
            }
        )
    return rows


def collect_us_snapshot(symbols: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    data = yf.download(symbols, period="2d", interval="1d", auto_adjust=True, progress=False, threads=True)
    for symbol in symbols:
        try:
            close = data[("Close", symbol)].dropna()
            volume = data[("Volume", symbol)].dropna()
            if close.empty:
                continue
            change_pct = None
            if len(close) >= 2 and float(close.iloc[-2]) > 0:
                change_pct = round((float(close.iloc[-1]) - float(close.iloc[-2])) / float(close.iloc[-2]) * 100, 2)
            results.append(
                {
                    "symbol": symbol,
                    "market": "US",
                    "snapshot_date": close.index[-1].date().isoformat(),
                    "close": float(close.iloc[-1]),
                    "change_pct": change_pct,
                    "market_cap": None,
                    "volume": None if volume.empty else int(volume.iloc[-1]),
                    "per": None,
                    "pbr": None,
                    "payload": {"price_source": "yfinance"},
                }
            )
        except Exception:
            continue
    return results
