from datetime import datetime, timedelta, timezone

from services.supabase_cache_service import CACHE_VALID_HOURS, is_fresh


def test_cache_valid_hours_is_20_for_direct_read_gate():
    assert CACHE_VALID_HOURS == 20


def test_is_fresh_accepts_rows_inside_20_hour_window():
    fresh_time = (datetime.now(timezone.utc) - timedelta(hours=19)).isoformat()
    assert is_fresh(fresh_time) is True


def test_is_fresh_rejects_rows_outside_20_hour_window():
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=21)).isoformat()
    assert is_fresh(stale_time) is False
