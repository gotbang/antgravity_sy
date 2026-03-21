from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.supabase_client import get_supabase
from services.kr_market_ingestion import collect_kr_market_snapshot, collect_kr_universe
from services.kr_fundamentals_ingestion import collect_kr_fundamentals
from services.market_summary_builder import build_market_summary
from services.supabase_cache_service import upsert_json
from services.us_market_ingestion import collect_us_snapshot, collect_us_universe


def _upsert_rows(table: str, rows: list[dict], conflict: str) -> int:
    client = get_supabase()
    total = 0
    for row in rows:
        client.table(table).upsert(row, on_conflict=conflict).execute()
        total += 1
    return total


def refresh_all() -> None:
    kr_universe = collect_kr_universe()
    us_universe = collect_us_universe()
    _upsert_rows('ticker_universe', kr_universe + us_universe, 'symbol,market')

    kr_snapshot = collect_kr_market_snapshot()
    us_symbols = [row['symbol'] for row in us_universe[:100]]
    us_snapshot = collect_us_snapshot(us_symbols)
    _upsert_rows('market_snapshot_daily', kr_snapshot + us_snapshot, 'symbol,snapshot_date')

    if kr_universe:
        first_symbol = kr_universe[0]['symbol'].replace('.KS', '')
        try:
            payload = collect_kr_fundamentals(first_symbol, '2025')
            upsert_json('fundamentals_cache', {'symbol': kr_universe[0]['symbol'], 'payload': payload}, 'symbol')
        except Exception:
            pass

    summary = build_market_summary(kr_snapshot + us_snapshot)
    upsert_json('market_summary_cache', {'cache_key': 'home', 'payload': summary}, 'cache_key')
    upsert_json('market_summary_cache', {'cache_key': 'trending', 'payload': {'items': (kr_snapshot + us_snapshot)[:10]}}, 'cache_key')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['all', 'fundamentals', 'summary'], default='all')
    args = parser.parse_args()
    refresh_all()
