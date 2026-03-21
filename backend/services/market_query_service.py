from __future__ import annotations

from services.cache_policy import should_live_fetch
from services.market_summary_builder import build_market_summary
from services.supabase_cache_service import read_json


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
    return {'items': [], 'query': query}


def load_stock_detail(symbol: str) -> dict:
    cached = read_json('fundamentals_cache', 'symbol', symbol)
    if cached:
        return cached
    if not should_live_fetch('price'):
        raise RuntimeError('stock cache unavailable')
    return {'symbol': symbol, 'price': None, 'summary': None}
