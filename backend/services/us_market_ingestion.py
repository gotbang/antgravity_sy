from __future__ import annotations

from typing import Any

import httpx
import yfinance as yf

US_FALLBACK_SYMBOLS = ("AAPL", "TSLA")


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


def _fetch_yahoo_chart_snapshot(symbol: str) -> dict[str, Any] | None:
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d&includeAdjustedClose=true'
    response = httpx.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()

    payload = response.json()
    result = (payload.get('chart', {}) or {}).get('result') or []
    if not result:
        return None

    row = result[0]
    timestamps = row.get('timestamp') or []
    quote = ((row.get('indicators') or {}).get('quote') or [{}])[0]
    closes = quote.get('close') or []
    volumes = quote.get('volume') or []

    valid_points = [
        (timestamps[index], closes[index], volumes[index] if index < len(volumes) else None)
        for index in range(min(len(timestamps), len(closes)))
        if closes[index] is not None
    ]
    if not valid_points:
        return None

    last_ts, last_close, last_volume = valid_points[-1]
    previous_close = valid_points[-2][1] if len(valid_points) >= 2 else None
    change_pct = None
    if previous_close not in (None, 0):
        change_pct = round((float(last_close) - float(previous_close)) / float(previous_close) * 100, 2)

    snapshot_date = valid_points[-1][0]
    from datetime import datetime, timezone
    snapshot_date = datetime.fromtimestamp(snapshot_date, tz=timezone.utc).date().isoformat()
    return {
        'symbol': symbol,
        'market': 'US',
        'snapshot_date': snapshot_date,
        'close': float(last_close),
        'change_pct': change_pct,
        'market_cap': None,
        'volume': None if last_volume is None else int(last_volume),
        'per': None,
        'pbr': None,
        'payload': {'price_source': 'yahoo_chart_api'},
    }


def collect_us_snapshot(symbols: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    try:
        data = yf.download(symbols, period="2d", interval="1d", auto_adjust=True, progress=False, threads=True)
    except Exception:
        data = None
    for symbol in symbols:
        try:
            if data is None:
                raise RuntimeError("yfinance unavailable")
            close = data[("Close", symbol)].dropna()
            volume = data[("Volume", symbol)].dropna()
            if close.empty:
                raise RuntimeError("empty close")
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
            if symbol not in US_FALLBACK_SYMBOLS:
                continue
            try:
                fallback_row = _fetch_yahoo_chart_snapshot(symbol)
            except Exception:
                fallback_row = None
            if fallback_row:
                results.append(fallback_row)
    return results
