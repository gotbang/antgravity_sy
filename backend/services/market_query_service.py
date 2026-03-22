from __future__ import annotations

from typing import Any

import httpx

from core.supabase_client import get_supabase
from services.cache_policy import should_live_fetch
from services.market_summary_builder import build_market_summary
from services.supabase_cache_service import read_json


def _search_rank(item: dict[str, Any], query: str) -> tuple[int, str, str]:
    safe_query = query.strip().lower()
    symbol = str(item.get('symbol') or '').lower()
    name = str(item.get('name') or '').lower()
    search_text = f'{symbol} {name}'.strip()

    if symbol == safe_query:
        return (0, symbol, name)
    if symbol.startswith(safe_query):
        return (1, symbol, name)
    if name.startswith(safe_query):
        return (2, symbol, name)
    if safe_query in search_text:
        return (3, symbol, name)
    return (4, symbol, name)


def _coerce_payload(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    payload = row.get("payload")
    return payload if isinstance(payload, dict) else {}


def _load_latest_snapshot(symbol: str) -> dict[str, Any] | None:
    result = (
        get_supabase()
        .table("market_snapshot_daily")
        .select("symbol, market, snapshot_date, close, change_pct, market_cap, volume, per, pbr, payload")
        .eq("symbol", symbol)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def _load_universe_row(symbol: str) -> dict[str, Any] | None:
    result = (
        get_supabase()
        .table("ticker_universe")
        .select("symbol, market, name, sector, industry")
        .eq("symbol", symbol)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def _fetch_yahoo_chart_price(symbol: str) -> dict[str, Any] | None:
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

    snapshot_date = httpx.Timestamp(last_ts).datetime.date().isoformat() if hasattr(httpx, 'Timestamp') else None
    if snapshot_date is None:
        from datetime import datetime, timezone
        snapshot_date = datetime.fromtimestamp(last_ts, tz=timezone.utc).date().isoformat()

    return {
        'symbol': symbol,
        'price': float(last_close),
        'change_pct': change_pct,
        'volume': None if last_volume is None else int(last_volume),
        'snapshot_date': snapshot_date,
        'payload': {'price_source': 'yahoo_chart_api'},
    }


def load_market_summary() -> dict:
    cached = read_json('market_summary_cache', 'cache_key', 'home')
    if cached:
        return cached
    if not should_live_fetch('summary'):
        raise RuntimeError('market summary cache unavailable')
    return build_market_summary([])


def load_trending() -> dict:
    cached = read_json('market_summary_cache', 'cache_key', 'trending')
    if cached:
        return cached
    if not should_live_fetch('price'):
        raise RuntimeError('trending cache unavailable')
    return {'items': []}


def load_stock_search(query: str) -> dict:
    cached = read_json('market_summary_cache', 'cache_key', f'search:{query.lower()}')
    if cached:
        return cached

    result = (
        get_supabase()
        .table("ticker_universe")
        .select("symbol, market, name, sector, industry")
        .or_(f"symbol.ilike.%{query}%,name.ilike.%{query}%")
        .limit(10)
        .execute()
    )
    items = sorted(result.data or [], key=lambda item: _search_rank(item, query))
    return {'items': items, 'query': query}


def load_stock_detail(symbol: str) -> dict:
    fundamentals = read_json('fundamentals_cache', 'symbol', symbol) or {}
    snapshot = _load_latest_snapshot(symbol)
    universe_row = _load_universe_row(symbol)

    if not snapshot and fundamentals:
        return fundamentals

    if not snapshot and universe_row:
        live_snapshot = None
        if symbol.endswith('.KS') and should_live_fetch('price'):
            try:
                live_snapshot = _fetch_yahoo_chart_price(symbol)
            except Exception:
                live_snapshot = None

        if live_snapshot:
            return {
                'symbol': symbol,
                'name': universe_row.get('name') or symbol,
                'market': universe_row.get('market'),
                'price': live_snapshot.get('price'),
                'change_pct': live_snapshot.get('change_pct'),
                'market_cap': None,
                'volume': live_snapshot.get('volume'),
                'per': None,
                'pbr': None,
                'snapshot_date': live_snapshot.get('snapshot_date'),
                'summary': fundamentals.get('summary'),
                'payload': live_snapshot.get('payload') or {},
            }

        return {
            'symbol': symbol,
            'name': universe_row.get('name') or symbol,
            'market': universe_row.get('market'),
            'price': None,
            'change_pct': None,
            'market_cap': None,
            'volume': None,
            'per': None,
            'pbr': None,
            'snapshot_date': None,
            'summary': fundamentals.get('summary'),
            'payload': {},
        }

    if not snapshot:
        if not should_live_fetch('price'):
            raise RuntimeError('stock cache unavailable')
        return {'symbol': symbol, 'price': None, 'summary': None}

    payload = _coerce_payload(snapshot)
    summary = fundamentals.get('aiSummary') or fundamentals.get('summary')

    return {
        'symbol': symbol,
        'name': (universe_row or {}).get('name') or fundamentals.get('company_name') or symbol,
        'market': snapshot.get('market') or (universe_row or {}).get('market'),
        'price': snapshot.get('close'),
        'change_pct': snapshot.get('change_pct'),
        'market_cap': snapshot.get('market_cap'),
        'volume': snapshot.get('volume'),
        'per': snapshot.get('per'),
        'pbr': snapshot.get('pbr'),
        'snapshot_date': snapshot.get('snapshot_date'),
        'summary': summary,
        'payload': payload,
    }
