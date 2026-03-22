from scripts import daily_refresh


def test_daily_refresh_skips_summary_overwrite_when_snapshots_are_empty(monkeypatch):
    upserts = []

    monkeypatch.setattr(daily_refresh, '_clear_broken_proxy_env', lambda: None)
    monkeypatch.setattr(daily_refresh, 'collect_kr_universe', lambda: [])
    monkeypatch.setattr(daily_refresh, 'collect_us_universe', lambda: [])
    monkeypatch.setattr(daily_refresh, 'collect_kr_snapshot', lambda _symbols: [])
    monkeypatch.setattr(daily_refresh, 'collect_us_snapshot', lambda _symbols: [])
    monkeypatch.setattr(daily_refresh, '_upsert_rows', lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(daily_refresh, '_insert_failure_logs', lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(daily_refresh, '_load_state_rows', lambda *args, **kwargs: [])
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

    rows = daily_refresh._build_detail_cache_rows(snapshot_rows, universe_rows, {'fearGreedIndex': 48})

    assert rows[0]['payload']['summary'] is not None
    assert 'Apple Inc.' in rows[0]['payload']['summary']
    assert '2026-03-20' in rows[0]['payload']['summary']
    assert rows[0]['payload']['price'] == 247.99
    assert rows[0]['payload']['price_status'] == 'live'
    assert 1.5 <= rows[0]['payload']['safe_activity_radius_pct'] <= 6.0


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


def test_daily_refresh_builds_home_summary_from_merged_snapshot_rows(monkeypatch):
    upserts = []

    monkeypatch.setattr(daily_refresh, '_clear_broken_proxy_env', lambda: None)
    monkeypatch.setattr(daily_refresh, 'collect_kr_universe', lambda: [{'symbol': '000660.KS', 'market': 'KR', 'name': 'SK하이닉스'}])
    monkeypatch.setattr(daily_refresh, 'collect_us_universe', lambda: [{'symbol': 'AAPL', 'market': 'US', 'name': 'Apple Inc.'}])
    monkeypatch.setattr(daily_refresh, 'collect_kr_snapshot', lambda _symbols: [{'symbol': '000660.KS', 'market': 'KR', 'snapshot_date': '2026-03-20', 'close': 100, 'change_pct': 1.5, 'market_cap': None, 'volume': 1, 'per': None, 'pbr': None}])
    monkeypatch.setattr(daily_refresh, 'collect_us_snapshot', lambda _symbols: [])
    monkeypatch.setattr(daily_refresh, '_upsert_rows', lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(daily_refresh, '_insert_failure_logs', lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(daily_refresh, '_load_state_rows', lambda *args, **kwargs: [])
    monkeypatch.setattr(daily_refresh, 'collect_kr_fundamentals', lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("skip fundamentals")))
    monkeypatch.setattr(
        daily_refresh,
        '_load_existing_snapshot_rows',
        lambda *args, **kwargs: [{'symbol': 'AAPL', 'market': 'US', 'snapshot_date': '2026-03-20', 'close': 200, 'change_pct': -2.0, 'market_cap': None, 'volume': 1, 'per': None, 'pbr': None}],
    )
    monkeypatch.setattr(daily_refresh, 'upsert_json', lambda table, row, conflict: upserts.append((table, row, conflict)))

    daily_refresh.refresh_all()

    home_rows = [row for table, row, _conflict in upserts if table == 'market_summary_cache' and row.get('cache_key') == 'home']
    assert len(home_rows) == 1
    payload = home_rows[0]['payload']
    assert payload['advancers'] == 1
    assert payload['decliners'] == 1


def test_merge_snapshot_rows_reuses_previous_price_when_primary_row_is_missing_values():
    primary_rows = [
        {'symbol': 'AAPL', 'snapshot_date': '2026-03-21', 'close': None, 'change_pct': None, 'volume': None},
    ]
    fallback_rows = [
        {'symbol': 'AAPL', 'snapshot_date': '2026-03-20', 'close': 200, 'change_pct': -1.5, 'volume': 500},
    ]

    rows = daily_refresh._merge_snapshot_rows(primary_rows, fallback_rows)

    assert rows[0]['close'] == 200
    assert rows[0]['change_pct'] == -1.5
    assert rows[0]['snapshot_date'] == '2026-03-21'


def test_daily_refresh_keeps_existing_snapshots_without_forcing_detail_cache_rebuild(monkeypatch):
    upserts = []

    monkeypatch.setattr(daily_refresh, '_clear_broken_proxy_env', lambda: None)
    monkeypatch.setattr(daily_refresh, 'collect_kr_universe', lambda: [{'symbol': '000660.KS', 'market': 'KR', 'name': 'SK하이닉스'}])
    monkeypatch.setattr(
        daily_refresh,
        'collect_us_universe',
        lambda: [
            {'symbol': 'AAPL', 'market': 'US', 'name': 'Apple Inc.'},
            {'symbol': 'TSLA', 'market': 'US', 'name': 'Tesla, Inc.'},
        ],
    )
    monkeypatch.setattr(daily_refresh, 'collect_kr_snapshot', lambda _symbols: [])
    monkeypatch.setattr(daily_refresh, 'collect_us_snapshot', lambda _symbols: [])
    def fake_upsert_rows(table, rows, _conflict):
        for row in rows:
            upserts.append((table, row, _conflict))
        return len(rows)

    monkeypatch.setattr(daily_refresh, '_upsert_rows', fake_upsert_rows)
    monkeypatch.setattr(daily_refresh, '_insert_failure_logs', lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(daily_refresh, '_load_state_rows', lambda *args, **kwargs: [])
    monkeypatch.setattr(daily_refresh, 'collect_kr_fundamentals', lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("skip fundamentals")))
    monkeypatch.setattr(
        daily_refresh,
        '_load_existing_snapshot_rows',
        lambda *args, **kwargs: [
            {'symbol': 'AAPL', 'market': 'US', 'snapshot_date': '2026-03-20', 'close': 201.1, 'change_pct': 1.0, 'market_cap': None, 'volume': 50000, 'per': None, 'pbr': None},
            {'symbol': 'TSLA', 'market': 'US', 'snapshot_date': '2026-03-20', 'close': 299.1, 'change_pct': -2.5, 'market_cap': None, 'volume': 60000, 'per': None, 'pbr': None},
            {'symbol': '000660.KS', 'market': 'KR', 'snapshot_date': '2026-03-20', 'close': 100000, 'change_pct': 0.3, 'market_cap': None, 'volume': 70000, 'per': None, 'pbr': None},
        ],
    )
    monkeypatch.setattr(daily_refresh, 'upsert_json', lambda table, row, conflict: upserts.append((table, row, conflict)))

    daily_refresh.refresh_all()

    detail_rows = [row for table, row, _conflict in upserts if table == 'fundamentals_cache']
    summary_rows = [row for table, row, _conflict in upserts if table == 'market_summary_cache']

    assert detail_rows == []
    assert summary_rows == []
