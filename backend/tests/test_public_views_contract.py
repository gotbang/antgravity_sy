from pathlib import Path


MIGRATION_PATH = Path(__file__).resolve().parents[2] / 'supabase' / 'migrations' / '20260322_public_market_views.sql'


def test_public_views_migration_declares_all_expected_views():
    migration = MIGRATION_PATH.read_text(encoding='utf-8')

    assert 'create or replace view public.v_home_summary as' in migration
    assert 'create or replace view public.v_stock_search as' in migration
    assert 'create or replace view public.v_stock_detail_latest as' in migration


def test_public_views_migration_locks_base_tables_and_grants_views():
    migration = MIGRATION_PATH.read_text(encoding='utf-8')

    assert 'alter table if exists public.ticker_universe enable row level security;' in migration
    assert 'alter table if exists public.market_snapshot_daily enable row level security;' in migration
    assert 'revoke all on table public.ticker_universe from anon, authenticated;' in migration
    assert 'grant select on public.v_home_summary to anon, authenticated;' in migration
    assert 'grant select on public.v_stock_search to anon, authenticated;' in migration
    assert 'grant select on public.v_stock_detail_latest to anon, authenticated;' in migration
