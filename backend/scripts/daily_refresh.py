from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.supabase_client import get_supabase
from services.kr_market_ingestion import collect_kr_market_snapshot, collect_kr_universe
from services.kr_fundamentals_ingestion import collect_kr_fundamentals
from services.market_summary_builder import build_market_summary
from services.supabase_cache_service import upsert_json
from services.us_market_ingestion import collect_us_snapshot, collect_us_universe

_UPSERT_CHUNK_SIZE = 200
REQUIRED_QUALITY_GATE_SYMBOLS = ("AAPL", "TSLA", "000660.KS")


def _clear_broken_proxy_env() -> None:
    broken_proxy_values = {
        'http://127.0.0.1:9',
        'https://127.0.0.1:9',
    }
    for key in (
        'HTTP_PROXY',
        'HTTPS_PROXY',
        'ALL_PROXY',
        'http_proxy',
        'https_proxy',
        'all_proxy',
        'GIT_HTTP_PROXY',
        'GIT_HTTPS_PROXY',
    ):
        value = os.environ.get(key)
        if value and value.lower() in broken_proxy_values:
            os.environ.pop(key, None)


def _chunk_rows(rows: list[dict], size: int = _UPSERT_CHUNK_SIZE) -> list[list[dict]]:
    return [rows[index:index + size] for index in range(0, len(rows), size)]


def _upsert_rows(table: str, rows: list[dict], conflict: str) -> int:
    if not rows:
        return 0

    client = get_supabase()
    total = 0
    for chunk in _chunk_rows(rows):
        client.table(table).upsert(chunk, on_conflict=conflict).execute()
        total += len(chunk)
    return total


def _build_detail_cache_rows(snapshot_rows: list[dict], universe_rows: list[dict]) -> list[dict]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    universe_map = {row['symbol']: row for row in universe_rows}
    rows: list[dict] = []
    for snapshot in snapshot_rows:
        symbol = snapshot['symbol']
        universe = universe_map.get(symbol, {})
        rows.append(
            {
                'symbol': symbol,
                'payload': {
                    'symbol': symbol,
                    'name': universe.get('name') or symbol,
                    'market': snapshot.get('market') or universe.get('market'),
                    'price': snapshot.get('close'),
                    'change_pct': snapshot.get('change_pct'),
                    'market_cap': snapshot.get('market_cap'),
                    'volume': snapshot.get('volume'),
                    'per': snapshot.get('per'),
                    'pbr': snapshot.get('pbr'),
                    'snapshot_date': snapshot.get('snapshot_date'),
                    'summary': None,
                },
                'fetched_at': fetched_at,
            }
        )
    return rows


def _load_existing_snapshot_rows(limit: int = 100) -> list[dict]:
    result = (
        get_supabase()
        .table('market_snapshot_daily')
        .select('symbol, market, snapshot_date, close, change_pct, market_cap, volume, per, pbr, payload')
        .order('snapshot_date', desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def _has_required_quality_gate_rows(snapshot_rows: list[dict]) -> bool:
    symbols = {row.get('symbol') for row in snapshot_rows}
    return all(symbol in symbols for symbol in REQUIRED_QUALITY_GATE_SYMBOLS)


def refresh_all() -> None:
    _clear_broken_proxy_env()

    kr_universe = collect_kr_universe()
    us_universe = collect_us_universe()
    ticker_universe = kr_universe + us_universe
    _upsert_rows('ticker_universe', ticker_universe, 'symbol,market')

    kr_snapshot = collect_kr_market_snapshot()
    us_symbols = [row['symbol'] for row in us_universe[:100]]
    us_snapshot = collect_us_snapshot(us_symbols)
    all_snapshots = kr_snapshot + us_snapshot
    _upsert_rows('market_snapshot_daily', all_snapshots, 'symbol,snapshot_date')

    detail_source_rows = all_snapshots or _load_existing_snapshot_rows()
    detail_rows = _build_detail_cache_rows(detail_source_rows, ticker_universe)
    _upsert_rows('fundamentals_cache', detail_rows, 'symbol')

    if kr_universe:
        first_symbol = kr_universe[0]['symbol'].replace('.KS', '')
        try:
            payload = collect_kr_fundamentals(first_symbol, '2025')
            upsert_json('fundamentals_cache', {'symbol': kr_universe[0]['symbol'], 'payload': payload}, 'symbol')
        except Exception:
            pass

    if all_snapshots:
        summary = build_market_summary(all_snapshots)
        upsert_json('market_summary_cache', {'cache_key': 'home', 'payload': summary}, 'cache_key')
        upsert_json('market_summary_cache', {'cache_key': 'trending', 'payload': {'items': all_snapshots[:10]}}, 'cache_key')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['all', 'fundamentals', 'summary'], default='all')
    args = parser.parse_args()
    refresh_all()
