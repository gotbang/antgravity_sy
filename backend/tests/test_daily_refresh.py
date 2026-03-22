from scripts import daily_refresh


def test_daily_refresh_skips_summary_overwrite_when_snapshots_are_empty(monkeypatch):
    upserts = []

    monkeypatch.setattr(daily_refresh, '_clear_broken_proxy_env', lambda: None)
    monkeypatch.setattr(daily_refresh, 'collect_kr_universe', lambda: [])
    monkeypatch.setattr(daily_refresh, 'collect_us_universe', lambda: [])
    monkeypatch.setattr(daily_refresh, 'collect_kr_market_snapshot', lambda: [])
    monkeypatch.setattr(daily_refresh, 'collect_us_snapshot', lambda _symbols: [])
    monkeypatch.setattr(daily_refresh, '_upsert_rows', lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(daily_refresh, '_load_existing_snapshot_rows', lambda *args, **kwargs: [])
    monkeypatch.setattr(daily_refresh, 'upsert_json', lambda table, row, conflict: upserts.append((table, row, conflict)))

    daily_refresh.refresh_all()

    cache_keys = [row.get('cache_key') for table, row, _conflict in upserts if table == 'market_summary_cache']
    assert 'home' not in cache_keys
    assert 'trending' not in cache_keys


def test_build_detail_cache_rows_populates_fallback_summary():
    snapshot_rows = [
        {
            'symbol': 'AAPL',
            'market': 'US',
            'snapshot_date': '2026-03-20',
            'close': 247.99,
            'change_pct': -0.39,
            'market_cap': None,
            'volume': 100,
            'per': 28.5,
            'pbr': 12.3,
        }
    ]
    universe_rows = [
        {
            'symbol': 'AAPL',
            'market': 'US',
            'name': 'Apple Inc.',
        }
    ]

    rows = daily_refresh._build_detail_cache_rows(snapshot_rows, universe_rows)

    assert rows[0]['payload']['summary'] is not None
    assert 'Apple Inc.' in rows[0]['payload']['summary']
    assert '2026-03-20' in rows[0]['payload']['summary']


def test_merge_snapshot_rows_keeps_fallback_symbols_when_primary_is_partial():
    primary_rows = [
        {'symbol': '000660.KS', 'snapshot_date': '2026-03-20'},
    ]
    fallback_rows = [
        {'symbol': 'AAPL', 'snapshot_date': '2026-03-20'},
        {'symbol': 'TSLA', 'snapshot_date': '2026-03-20'},
    ]

    rows = daily_refresh._merge_snapshot_rows(primary_rows, fallback_rows)
    symbols = {row['symbol'] for row in rows}

    assert symbols == {'AAPL', 'TSLA', '000660.KS'}
