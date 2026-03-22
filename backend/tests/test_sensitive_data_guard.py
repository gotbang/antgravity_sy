from pathlib import Path


MIGRATION_PATH = Path(__file__).resolve().parents[2] / 'supabase' / 'migrations' / '20260322_public_market_views.sql'


def test_public_views_do_not_grant_base_table_access_to_browser_roles():
    migration = MIGRATION_PATH.read_text(encoding='utf-8')

    assert 'revoke all on table public.ticker_universe from anon, authenticated;' in migration
    assert 'revoke all on table public.market_snapshot_daily from anon, authenticated;' in migration


def test_public_views_do_not_expose_payload_or_fetched_at_columns():
    migration = MIGRATION_PATH.read_text(encoding='utf-8')

    assert 'payload->>' in migration
    assert 'select("payload' not in migration
    assert 'fetched_at as fetched_at' not in migration
