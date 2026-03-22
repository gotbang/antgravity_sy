from __future__ import annotations

from datetime import datetime, timedelta, timezone

from scripts import daily_refresh


def test_assign_coverage_tiers_marks_top_200_per_market_as_hot():
    universe_rows = [
        {"symbol": f"KR{i:03d}.KS", "market": "KR", "name": f"KR {i}"}
        for i in range(205)
    ] + [
        {"symbol": f"US{i:03d}", "market": "US", "name": f"US {i}"}
        for i in range(205)
    ]
    state_rows = []
    ranking_rows = [
        {"symbol": f"KR{i:03d}.KS", "market": "KR", "market_cap": 10_000 - i, "volume": 1_000 - i}
        for i in range(205)
    ] + [
        {"symbol": f"US{i:03d}", "market": "US", "market_cap": 20_000 - i, "volume": 2_000 - i}
        for i in range(205)
    ]

    assigned = daily_refresh._assign_coverage_tiers(universe_rows, ranking_rows, state_rows)

    kr_hot = [row for row in assigned if row["market"] == "KR" and row["coverage_tier"] == "hot"]
    us_hot = [row for row in assigned if row["market"] == "US" and row["coverage_tier"] == "hot"]

    assert len(kr_hot) == 200
    assert len(us_hot) == 200
    assert any(row["symbol"] == "KR204.KS" and row["coverage_tier"] != "hot" for row in assigned)
    assert any(row["symbol"] == "US204" and row["coverage_tier"] != "hot" for row in assigned)


def test_assign_coverage_tiers_marks_recent_non_hot_symbols_as_warm():
    now = datetime.now(timezone.utc)
    universe_rows = [
        {"symbol": "HOT1", "market": "US", "name": "Hot 1"},
        {"symbol": "WARM1", "market": "US", "name": "Warm 1"},
        {"symbol": "COLD1", "market": "US", "name": "Cold 1"},
    ]
    ranking_rows = [
        {"symbol": "HOT1", "market": "US", "market_cap": 300, "volume": 300},
        {"symbol": "WARM1", "market": "US", "market_cap": 200, "volume": 200},
        {"symbol": "COLD1", "market": "US", "market_cap": 100, "volume": 100},
    ]
    state_rows = [
        {"symbol": "WARM1", "market": "US", "last_succeeded_at": (now - timedelta(days=3)).isoformat()},
        {"symbol": "COLD1", "market": "US", "last_succeeded_at": (now - timedelta(days=30)).isoformat()},
    ]

    assigned = daily_refresh._assign_coverage_tiers(universe_rows, ranking_rows, state_rows, hot_count=1)
    tiers = {row["symbol"]: row["coverage_tier"] for row in assigned}

    assert tiers["HOT1"] == "hot"
    assert tiers["WARM1"] == "warm"
    assert tiers["COLD1"] == "cold"


def test_assign_coverage_tiers_keeps_refresh_bucket_within_twelve_slots():
    universe_rows = [{"symbol": f"SYM{i}", "market": "US", "name": f"Name {i}"} for i in range(30)]
    ranking_rows = [{"symbol": f"SYM{i}", "market": "US", "market_cap": 300 - i, "volume": 300 - i} for i in range(30)]

    assigned = daily_refresh._assign_coverage_tiers(universe_rows, ranking_rows, [], hot_count=2)

    for row in assigned:
        if row["coverage_tier"] == "warm":
            assert 0 <= row["refresh_bucket"] <= 11


def test_determine_freshness_status_returns_fresh_stale_and_missing():
    now = datetime.now(timezone.utc)

    fresh = daily_refresh._determine_freshness_status(
        close=100,
        fetched_at=(now - timedelta(hours=1)).isoformat(),
        now_utc=now,
    )
    stale = daily_refresh._determine_freshness_status(
        close=100,
        fetched_at=(now - timedelta(hours=25)).isoformat(),
        now_utc=now,
    )
    missing = daily_refresh._determine_freshness_status(close=None, fetched_at=None, now_utc=now)

    assert fresh == "fresh"
    assert stale == "stale"
    assert missing == "missing"


def test_resolve_kr_price_provider_prefers_krx_when_key_is_available(monkeypatch):
    monkeypatch.setattr(daily_refresh.settings, "KRX_AUTH_KEY", "test-key")

    assert daily_refresh.resolve_kr_price_provider() == "krx_official"


def test_resolve_kr_price_provider_falls_back_to_yfinance_without_key(monkeypatch):
    monkeypatch.setattr(daily_refresh.settings, "KRX_AUTH_KEY", "")

    assert daily_refresh.resolve_kr_price_provider() == "yfinance_fallback"


def test_build_scheduled_phases_includes_daily_and_warm_slots():
    current = datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc)

    phases = daily_refresh._resolve_scheduled_phases(current)

    assert "universe-sync" in phases
    assert "warm-rotate" in phases


def test_build_scheduled_phases_skips_warm_when_not_even_hour():
    current = datetime(2026, 3, 23, 1, 30, tzinfo=timezone.utc)

    phases = daily_refresh._resolve_scheduled_phases(current)

    assert "warm-rotate" not in phases


def test_exact_worker_processes_only_queued_requests(monkeypatch):
    updates = []
    monkeypatch.setattr(
        daily_refresh,
        "_load_queued_refresh_requests",
        lambda limit=20: [
            {"symbol": "AAPL", "market": "US", "status": "queued", "priority": 100},
            {"symbol": "TSLA", "market": "US", "status": "done", "priority": 100},
        ],
    )
    monkeypatch.setattr(daily_refresh, "_mark_refresh_request_status", lambda symbol, status, error_code=None: updates.append((symbol, status, error_code)))
    monkeypatch.setattr(daily_refresh, "_load_existing_snapshot_rows", lambda *args, **kwargs: [])
    monkeypatch.setattr(daily_refresh, "_load_universe_rows", lambda: [{"symbol": "AAPL", "market": "US", "name": "Apple Inc.", "coverage_tier": "cold"}])
    monkeypatch.setattr(daily_refresh, "_load_state_rows", lambda: [])
    monkeypatch.setattr(daily_refresh, "_fetch_snapshots_for_symbols", lambda *args, **kwargs: ([{"symbol": "AAPL", "market": "US", "snapshot_date": "2026-03-23", "close": 200, "change_pct": 1.2, "volume": 1000, "market_cap": None, "per": None, "pbr": None, "payload": {"price_source": "yfinance"}}], []))
    monkeypatch.setattr(daily_refresh, "_upsert_rows", lambda *args, **kwargs: 0)
    monkeypatch.setattr(daily_refresh, "_upsert_state_rows", lambda rows: None)
    monkeypatch.setattr(daily_refresh, "_insert_failure_logs", lambda rows: None)
    monkeypatch.setattr(daily_refresh, "_rebuild_summary_from_sources", lambda *args, **kwargs: None)

    daily_refresh.run_exact_worker(run_id="test-run")

    assert updates == [("AAPL", "running", None), ("AAPL", "done", None)]
