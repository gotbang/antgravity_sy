from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.supabase_client import get_supabase
from services.activity_radius_policy import build_safe_activity_radius
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


def _build_stock_summary(snapshot: dict, universe: dict) -> str:
    name = universe.get('name') or snapshot.get('symbol') or '이 종목'
    market = snapshot.get('market') or universe.get('market') or 'UNKNOWN'
    snapshot_date = snapshot.get('snapshot_date') or '최근 영업일'
    change_pct = snapshot.get('change_pct')
    per = snapshot.get('per')
    pbr = snapshot.get('pbr')

    change_text = '등락률 데이터가 아직 없어.'
    if change_pct is not None:
        direction = '상승' if change_pct > 0 else '하락' if change_pct < 0 else '보합'
        change_text = f'{snapshot_date} 기준 {direction} {change_pct}% 흐름이야.'

    valuation_bits: list[str] = []
    if per is not None:
        valuation_bits.append(f'PER {per}')
    if pbr is not None:
        valuation_bits.append(f'PBR {pbr}')

    valuation_text = '밸류에이션 지표는 아직 비어 있어.'
    if valuation_bits:
        valuation_text = ', '.join(valuation_bits) + ' 기준으로 적재됐어.'

    return f'{name}({market}) 종목이야. {change_text} {valuation_text}'


def _build_detail_cache_rows(
    snapshot_rows: list[dict],
    universe_rows: list[dict],
    market_summary: dict | None = None,
) -> list[dict]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    universe_map = {row['symbol']: row for row in universe_rows}
    rows: list[dict] = []
    for snapshot in snapshot_rows:
        symbol = snapshot['symbol']
        universe = universe_map.get(symbol, {})
        activity_radius = build_safe_activity_radius(snapshot, market_summary)
        price = snapshot.get('close')
        rows.append(
            {
                'symbol': symbol,
                'payload': {
                    'symbol': symbol,
                    'name': universe.get('name') or symbol,
                    'market': snapshot.get('market') or universe.get('market'),
                    'price': price,
                    'change_pct': snapshot.get('change_pct'),
                    'market_cap': snapshot.get('market_cap'),
                    'volume': snapshot.get('volume'),
                    'per': snapshot.get('per'),
                    'pbr': snapshot.get('pbr'),
                    'snapshot_date': snapshot.get('snapshot_date'),
                    'summary': _build_stock_summary(snapshot, universe),
                    'price_status': 'live' if price is not None else 'missing',
                    'price_source': 'snapshot' if price is not None else 'unavailable',
                    **activity_radius,
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


def _merge_snapshot_rows(primary_rows: list[dict], fallback_rows: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for row in fallback_rows:
        symbol = row.get('symbol')
        if symbol:
            merged[symbol] = row
    for row in primary_rows:
        symbol = row.get('symbol')
        if symbol:
            existing = merged.get(symbol, {})
            merged[symbol] = {
                **existing,
                **row,
                'snapshot_date': row.get('snapshot_date') or existing.get('snapshot_date'),
                'close': row.get('close') if row.get('close') is not None else existing.get('close'),
                'change_pct': row.get('change_pct') if row.get('change_pct') is not None else existing.get('change_pct'),
                'market_cap': row.get('market_cap') if row.get('market_cap') is not None else existing.get('market_cap'),
                'volume': row.get('volume') if row.get('volume') is not None else existing.get('volume'),
                'per': row.get('per') if row.get('per') is not None else existing.get('per'),
                'pbr': row.get('pbr') if row.get('pbr') is not None else existing.get('pbr'),
                'payload': row.get('payload') or existing.get('payload'),
            }
    return list(merged.values())


def _has_required_quality_gate_rows(snapshot_rows: list[dict]) -> bool:
    row_map = {row.get('symbol'): row for row in snapshot_rows}
    return all(
        row_map.get(symbol) and row_map[symbol].get('close') is not None
        for symbol in REQUIRED_QUALITY_GATE_SYMBOLS
    )


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

    existing_snapshot_rows = _load_existing_snapshot_rows(limit=500)
    detail_source_rows = _merge_snapshot_rows(all_snapshots, existing_snapshot_rows)
    summary = build_market_summary(detail_source_rows) if detail_source_rows else None
    detail_rows = _build_detail_cache_rows(detail_source_rows, ticker_universe, summary)
    _upsert_rows('fundamentals_cache', detail_rows, 'symbol')
    detail_payload_map = {row['symbol']: row['payload'] for row in detail_rows}

    if kr_universe:
        first_symbol = kr_universe[0]['symbol'].replace('.KS', '')
        try:
            payload = collect_kr_fundamentals(first_symbol, '2025')
            merged_payload = {
                **detail_payload_map.get(kr_universe[0]['symbol'], {}),
                **payload,
            }
            upsert_json('fundamentals_cache', {'symbol': kr_universe[0]['symbol'], 'payload': merged_payload}, 'symbol')
        except Exception:
            pass

    if summary:
        upsert_json('market_summary_cache', {'cache_key': 'home', 'payload': summary}, 'cache_key')
        upsert_json('market_summary_cache', {'cache_key': 'trending', 'payload': {'items': detail_source_rows[:10]}}, 'cache_key')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['all', 'fundamentals', 'summary'], default='all')
    args = parser.parse_args()
    refresh_all()
