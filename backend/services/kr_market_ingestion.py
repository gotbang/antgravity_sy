from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import dartlab
import httpx
from pykrx import stock

KR_FALLBACK_SYMBOLS = ("000660.KS", "005930.KS")


def _resolve_kr_business_day(target_date: str | None = None) -> str | None:
    if target_date:
        normalized = target_date.replace("-", "")
        try:
            return stock.get_nearest_business_day_in_a_week(date=normalized, prev=True)
        except Exception:
            return None

    today = datetime.now()
    for offset in range(0, 14):
        candidate = (today - timedelta(days=offset)).strftime("%Y%m%d")
        try:
            resolved = stock.get_nearest_business_day_in_a_week(date=candidate, prev=True)
        except Exception:
            continue
        if resolved:
            return resolved

    return None


def collect_kr_market_snapshot(target_date: str | None = None) -> list[dict[str, Any]]:
    date_str = _resolve_kr_business_day(target_date)
    if not date_str:
        return _collect_kr_yahoo_fallback_snapshot()

    frame = stock.get_market_fundamental_by_ticker(date_str)
    ohlcv = stock.get_market_ohlcv_by_ticker(date_str)
    if frame.empty and ohlcv.empty:
        return _collect_kr_yahoo_fallback_snapshot()

    rows: list[dict[str, Any]] = []
    tickers = set(frame.index.tolist()) | set(ohlcv.index.tolist())
    for ticker in sorted(tickers):
        item = frame.loc[ticker] if ticker in frame.index else {}
        price_row = ohlcv.loc[ticker] if ticker in ohlcv.index else None
        rows.append(
            {
                "symbol": f"{ticker}.KS",
                "market": "KR",
                "snapshot_date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
                "close": None if price_row is None else float(price_row.get("종가", 0) or 0),
                "change_pct": None if price_row is None else float(price_row.get("등락률", 0) or 0),
                "market_cap": None,
                "volume": None if price_row is None else int(price_row.get("거래량", 0) or 0),
                "per": float(item.get("PER", 0) or 0) or None,
                "pbr": float(item.get("PBR", 0) or 0) or None,
                "payload": {
                    "price_source": "PyKRX",
                },
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

    snapshot_date = datetime.fromtimestamp(last_ts).date().isoformat()
    return {
        'symbol': symbol,
        'market': 'KR',
        'snapshot_date': snapshot_date,
        'close': float(last_close),
        'change_pct': change_pct,
        'market_cap': None,
        'volume': None if last_volume is None else int(last_volume),
        'per': None,
        'pbr': None,
        'payload': {
            'price_source': 'Yahoo chart API',
        },
    }


def _collect_kr_yahoo_fallback_snapshot() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol in KR_FALLBACK_SYMBOLS:
        try:
            snapshot = _fetch_yahoo_chart_snapshot(symbol)
        except Exception:
            snapshot = None
        if snapshot:
            rows.append(snapshot)
    return rows


def collect_kr_universe(target_date: str | None = None) -> list[dict[str, Any]]:
    date_str = _resolve_kr_business_day(target_date)
    rows: list[dict[str, Any]] = []

    if date_str:
        tickers = stock.get_market_ticker_list(date=date_str, market="ALL")
        for ticker in tickers:
            name = stock.get_market_ticker_name(ticker)
            rows.append(
                {
                    "symbol": f"{ticker}.KS",
                    "market": "KR",
                    "name": name,
                    "sector": None,
                    "industry": None,
                }
            )
        if rows:
            return rows

    try:
        listing = dartlab.listing()
        for item in listing.to_dicts():
            code = str(item.get("종목코드", "")).strip()
            if not code:
                continue
            rows.append(
                {
                    "symbol": f"{code}.KS",
                    "market": "KR",
                    "name": item.get("회사명"),
                    "sector": item.get("시장구분"),
                    "industry": item.get("업종"),
                }
            )
    except Exception:
        return []

    return rows
