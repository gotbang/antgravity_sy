from scripts import daily_refresh


def test_daily_refresh_skips_summary_overwrite_when_snapshots_are_empty(monkeypatch):
    upserts = []

    monkeypatch.setattr(daily_refresh, '_clear_broken_proxy_env', lambda: None)
    monkeypatch.setattr(daily_refresh, 'collect_kr_universe', lambda: [])
    monkeypatch.setattr(daily_refresh, 'collect_us_universe', lambda: [])
    monkeypatch.setattr(daily_refresh, 'collect_kr_market_snapshot', lambda: [])
    monkeypatch.setattr(daily_refresh, 'collect_us_snapshot', lambda _symbols: [])
    monkeypatch.setattr(daily_refresh, '_upsert_rows', lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(daily_refresh, '_load_existing_snapshot_rows', lambda: [])
    monkeypatch.setattr(daily_refresh, 'upsert_json', lambda table, row, conflict: upserts.append((table, row, conflict)))

    daily_refresh.refresh_all()

    cache_keys = [row.get('cache_key') for table, row, _conflict in upserts if table == 'market_summary_cache']
    assert 'home' not in cache_keys
    assert 'trending' not in cache_keys
