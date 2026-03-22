from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings
from core.supabase_client import get_supabase
from services.activity_radius_policy import build_safe_activity_radius
from services.kr_fundamentals_ingestion import collect_kr_fundamentals
from services.kr_market_ingestion import collect_kr_snapshot, collect_kr_universe, resolve_kr_price_provider
from services.market_summary_builder import build_market_summary
from services.supabase_cache_service import upsert_json
from services.us_market_ingestion import collect_us_snapshot, collect_us_universe

_UPSERT_CHUNK_SIZE = 200
REQUIRED_QUALITY_GATE_SYMBOLS = ("AAPL", "TSLA", "000660.KS")
DIRECT_READ_FRESHNESS_HOURS = 20
HOT_SYMBOL_COUNT = 200
WARM_BUCKET_COUNT = 12
EXACT_WORKER_BATCH_SIZE = 20
KST = ZoneInfo("Asia/Seoul")
EST = ZoneInfo("America/New_York")


def _clear_broken_proxy_env() -> None:
    broken_proxy_values = {
        "http://127.0.0.1:9",
        "https://127.0.0.1:9",
    }
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "GIT_HTTP_PROXY",
        "GIT_HTTPS_PROXY",
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


def _insert_rows(table: str, rows: list[dict]) -> int:
    if not rows:
        return 0

    client = get_supabase()
    total = 0
    for chunk in _chunk_rows(rows):
        client.table(table).insert(chunk).execute()
        total += len(chunk)
    return total


def _upsert_state_rows(rows: list[dict]) -> int:
    return _upsert_rows("symbol_ingestion_state", rows, "symbol,market")


def _insert_failure_logs(rows: list[dict]) -> int:
    return _insert_rows("symbol_ingestion_failure_log", rows)


def _load_universe_rows(limit: int = 10000) -> list[dict]:
    result = (
        get_supabase()
        .table("ticker_universe")
        .select("symbol, market, name, sector, industry, coverage_tier, coverage_rank, refresh_bucket, is_exact_refresh_enabled, primary_provider")
        .limit(limit)
        .execute()
    )
    return result.data or []


def _load_state_rows(limit: int = 10000) -> list[dict]:
    result = (
        get_supabase()
        .table("symbol_ingestion_state")
        .select("*")
        .limit(limit)
        .execute()
    )
    return result.data or []


def _load_queued_refresh_requests(limit: int = EXACT_WORKER_BATCH_SIZE) -> list[dict]:
    result = (
        get_supabase()
        .table("symbol_refresh_requests")
        .select("*")
        .eq("status", "queued")
        .order("priority")
        .order("requested_at")
        .limit(limit)
        .execute()
    )
    return result.data or []


def _mark_refresh_request_status(symbol: str, status: str, error_code: str | None = None) -> None:
    payload = {
        "status": status,
        "last_error_code": error_code,
    }
    if status == "running":
        payload["started_at"] = datetime.now(timezone.utc).isoformat()
    if status in {"done", "failed"}:
        payload["completed_at"] = datetime.now(timezone.utc).isoformat()

    get_supabase().table("symbol_refresh_requests").update(payload).eq("symbol", symbol).execute()


def _load_existing_snapshot_rows(limit: int = 10000) -> list[dict]:
    result = (
        get_supabase()
        .table("market_snapshot_daily")
        .select("symbol, market, snapshot_date, close, change_pct, market_cap, volume, per, pbr, payload, fetched_at")
        .order("snapshot_date", desc=True)
        .limit(limit)
        .execute()
    )
    rows = result.data or []

    latest_by_symbol: dict[str, dict] = {}
    for row in rows:
        symbol = row.get("symbol")
        if symbol and symbol not in latest_by_symbol:
            latest_by_symbol[symbol] = row
    return list(latest_by_symbol.values())


def _build_stock_summary(snapshot: dict, universe: dict) -> str:
    name = universe.get("name") or snapshot.get("symbol") or "이 종목"
    market = snapshot.get("market") or universe.get("market") or "UNKNOWN"
    snapshot_date = snapshot.get("snapshot_date") or "최근 영업일"
    change_pct = snapshot.get("change_pct")
    per = snapshot.get("per")
    pbr = snapshot.get("pbr")

    change_text = "등락률 데이터가 아직 없어."
    if change_pct is not None:
        direction = "상승" if change_pct > 0 else "하락" if change_pct < 0 else "보합"
        change_text = f"{snapshot_date} 기준 {direction} {change_pct}% 흐름이야."

    valuation_bits: list[str] = []
    if per is not None:
        valuation_bits.append(f"PER {per}")
    if pbr is not None:
        valuation_bits.append(f"PBR {pbr}")

    valuation_text = "밸류에이션 지표는 아직 비어 있어."
    if valuation_bits:
        valuation_text = ", ".join(valuation_bits) + " 기준으로 적재됐어."

    return f"{name}({market}) 종목이야. {change_text} {valuation_text}"


def _build_detail_cache_rows(
    snapshot_rows: list[dict],
    universe_rows: list[dict],
    market_summary: dict | None = None,
) -> list[dict]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    universe_map = {(row["symbol"], row.get("market")): row for row in universe_rows}
    rows: list[dict] = []
    for snapshot in snapshot_rows:
        symbol = snapshot["symbol"]
        universe = universe_map.get((symbol, snapshot.get("market"))) or {}
        activity_radius = build_safe_activity_radius(snapshot, market_summary)
        price = snapshot.get("close")
        rows.append(
            {
                "symbol": symbol,
                "payload": {
                    "symbol": symbol,
                    "name": universe.get("name") or symbol,
                    "market": snapshot.get("market") or universe.get("market"),
                    "price": price,
                    "change_pct": snapshot.get("change_pct"),
                    "market_cap": snapshot.get("market_cap"),
                    "volume": snapshot.get("volume"),
                    "per": snapshot.get("per"),
                    "pbr": snapshot.get("pbr"),
                    "snapshot_date": snapshot.get("snapshot_date"),
                    "summary": _build_stock_summary(snapshot, universe),
                    "price_status": "live" if price is not None else "missing",
                    "price_source": ((snapshot.get("payload") or {}).get("price_source") or "snapshot") if price is not None else "unavailable",
                    **activity_radius,
                },
                "fetched_at": fetched_at,
            }
        )
    return rows


def _merge_snapshot_rows(primary_rows: list[dict], fallback_rows: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for row in fallback_rows:
        symbol = row.get("symbol")
        if symbol:
            merged[symbol] = row
    for row in primary_rows:
        symbol = row.get("symbol")
        if symbol:
            existing = merged.get(symbol, {})
            merged[symbol] = {
                **existing,
                **row,
                "snapshot_date": row.get("snapshot_date") or existing.get("snapshot_date"),
                "close": row.get("close") if row.get("close") is not None else existing.get("close"),
                "change_pct": row.get("change_pct") if row.get("change_pct") is not None else existing.get("change_pct"),
                "market_cap": row.get("market_cap") if row.get("market_cap") is not None else existing.get("market_cap"),
                "volume": row.get("volume") if row.get("volume") is not None else existing.get("volume"),
                "per": row.get("per") if row.get("per") is not None else existing.get("per"),
                "pbr": row.get("pbr") if row.get("pbr") is not None else existing.get("pbr"),
                "payload": row.get("payload") or existing.get("payload"),
                "fetched_at": row.get("fetched_at") or existing.get("fetched_at"),
            }
    return list(merged.values())


def _has_required_quality_gate_rows(snapshot_rows: list[dict]) -> bool:
    row_map = {row.get("symbol"): row for row in snapshot_rows}
    return all(
        row_map.get(symbol) and row_map[symbol].get("close") is not None
        for symbol in REQUIRED_QUALITY_GATE_SYMBOLS
    )


def _stable_bucket(symbol: str) -> int:
    digest = hashlib.sha256(symbol.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % WARM_BUCKET_COUNT


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _determine_freshness_status(close: float | int | None, fetched_at: str | None, now_utc: datetime | None = None) -> str:
    if close is None:
        return "missing"
    if not fetched_at:
        return "stale"
    now_utc = now_utc or datetime.now(timezone.utc)
    fetched_at_dt = _parse_iso_timestamp(fetched_at)
    if fetched_at_dt is None:
        return "stale"
    max_age = timedelta(hours=DIRECT_READ_FRESHNESS_HOURS)
    return "fresh" if now_utc - fetched_at_dt <= max_age else "stale"


def _snapshot_datetime_iso(snapshot_date: str | None, fallback_now: datetime) -> str | None:
    if not snapshot_date:
        return None
    try:
        return datetime.fromisoformat(str(snapshot_date)).replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return fallback_now.isoformat()


def _assign_coverage_tiers(
    universe_rows: list[dict],
    ranking_rows: list[dict],
    state_rows: list[dict],
    hot_count: int = HOT_SYMBOL_COUNT,
) -> list[dict]:
    rank_map: dict[tuple[str, str], int] = {}
    rows_by_market: dict[str, list[dict]] = defaultdict(list)
    state_map = {(row.get("symbol"), row.get("market")): row for row in state_rows}
    now_utc = datetime.now(timezone.utc)
    recent_cutoff = now_utc - timedelta(days=14)

    for row in ranking_rows:
        rows_by_market[str(row.get("market"))].append(row)

    for market, rows in rows_by_market.items():
        sorted_rows = sorted(
            rows,
            key=lambda item: (
                -(item.get("market_cap") or 0),
                -(item.get("volume") or 0),
                str(item.get("symbol") or ""),
            ),
        )
        for index, row in enumerate(sorted_rows, start=1):
            rank_map[(row.get("symbol"), market)] = index

    assigned: list[dict] = []
    seen_ranks: dict[str, int] = defaultdict(int)
    for row in universe_rows:
        symbol = row["symbol"]
        market = row["market"]
        key = (symbol, market)
        rank = rank_map.get(key)
        if rank is None:
            seen_ranks[market] += 1
            rank = len([item for item in rank_map if item[1] == market]) + seen_ranks[market]
        previous_state = state_map.get(key) or {}
        last_succeeded_at = _parse_iso_timestamp(previous_state.get("last_succeeded_at"))
        is_recent = bool(last_succeeded_at and last_succeeded_at >= recent_cutoff)
        if rank <= hot_count:
            coverage_tier = "hot"
        elif is_recent:
            coverage_tier = "warm"
        else:
            coverage_tier = "cold"

        primary_provider = "krx_official" if market == "KR" and settings.KRX_AUTH_KEY.strip() else "yfinance"
        if market == "KR" and not settings.KRX_AUTH_KEY.strip():
            primary_provider = "yfinance_fallback"

        assigned.append(
            {
                **row,
                "coverage_tier": coverage_tier,
                "coverage_rank": rank,
                "refresh_bucket": _stable_bucket(symbol) if coverage_tier == "warm" else None,
                "is_exact_refresh_enabled": True,
                "primary_provider": primary_provider,
            }
        )
    return assigned


def _rebuild_summary_from_sources(
    universe_rows: list[dict] | None = None,
    current_snapshot_rows: list[dict] | None = None,
) -> None:
    current_universe = universe_rows or _load_universe_rows()
    existing_rows = _load_existing_snapshot_rows(limit=10000)
    latest_rows = _merge_snapshot_rows(current_snapshot_rows or [], existing_rows)
    if not latest_rows:
        return

    summary = build_market_summary(latest_rows)
    if not summary:
        return

    detail_rows = _build_detail_cache_rows(latest_rows, current_universe, summary)
    _upsert_rows("fundamentals_cache", detail_rows, "symbol")
    upsert_json("market_summary_cache", {"cache_key": "home", "payload": summary}, "cache_key")
    upsert_json("market_summary_cache", {"cache_key": "trending", "payload": {"items": latest_rows[:10]}}, "cache_key")


def _load_latest_snapshot_rows_for_ranking() -> list[dict]:
    return _load_existing_snapshot_rows(limit=10000)


def run_universe_sync(run_id: str) -> list[dict]:
    kr_universe = collect_kr_universe()
    us_universe = collect_us_universe()
    ticker_universe = kr_universe + us_universe
    ranking_rows = _load_latest_snapshot_rows_for_ranking()
    state_rows = _load_state_rows()
    assigned_rows = _assign_coverage_tiers(ticker_universe, ranking_rows, state_rows)
    _upsert_rows("ticker_universe", assigned_rows, "symbol,market")
    return assigned_rows


def _resolve_phase_symbol_rows(
    market: str | None = None,
    tier: str | None = None,
    bucket: int | None = None,
    universe_rows: list[dict] | None = None,
) -> list[dict]:
    rows = universe_rows if universe_rows is not None else _load_universe_rows()
    filtered: list[dict] = []
    for row in rows:
        if market and row.get("market") != market:
            continue
        if tier and row.get("coverage_tier") != tier:
            continue
        if bucket is not None and row.get("refresh_bucket") != bucket:
            continue
        filtered.append(row)
    return sorted(filtered, key=lambda item: (item.get("coverage_rank") or 999999, str(item.get("symbol") or "")))


def _build_failure_log_row(
    *,
    run_id: str,
    symbol: str,
    market: str,
    phase: str,
    provider: str | None,
    error_code: str,
    error_message: str,
) -> dict:
    return {
        "run_id": run_id,
        "symbol": symbol,
        "market": market,
        "phase": phase,
        "provider": provider,
        "result": "failure",
        "error_code": error_code,
        "error_message": error_message,
        "attempted_at": datetime.now(timezone.utc).isoformat(),
    }


def _fetch_snapshots_for_symbols(symbol_rows: list[dict], phase: str) -> tuple[list[dict], list[dict]]:
    by_market: dict[str, list[dict]] = defaultdict(list)
    for row in symbol_rows:
        by_market[str(row.get("market") or "")].append(row)

    snapshot_rows: list[dict] = []
    failure_logs: list[dict] = []

    for market, rows in by_market.items():
        symbols = [row["symbol"] for row in rows]
        try:
            if market == "KR":
                snapshot_rows.extend(collect_kr_snapshot(symbols))
            elif market == "US":
                snapshot_rows.extend(collect_us_snapshot(symbols))
        except Exception as exc:
            provider = resolve_kr_price_provider() if market == "KR" else "yfinance"
            for row in rows:
                failure_logs.append(
                    _build_failure_log_row(
                        run_id=_create_run_id("phase-error"),
                        symbol=row["symbol"],
                        market=market,
                        phase=phase,
                        provider=provider,
                        error_code="provider_exception",
                        error_message=str(exc),
                    )
                )
    return snapshot_rows, failure_logs


def _build_state_updates_for_attempts(
    symbol_rows: list[dict],
    snapshot_rows: list[dict],
    existing_state_rows: list[dict],
    *,
    phase: str,
    run_id: str,
) -> tuple[list[dict], list[dict]]:
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()
    existing_state_map = {(row.get("symbol"), row.get("market")): row for row in existing_state_rows}
    snapshot_map = {row.get("symbol"): row for row in snapshot_rows}
    state_rows: list[dict] = []
    failure_logs: list[dict] = []

    for symbol_row in symbol_rows:
        symbol = symbol_row["symbol"]
        market = symbol_row["market"]
        key = (symbol, market)
        existing = existing_state_map.get(key) or {}
        snapshot = snapshot_map.get(symbol)
        coverage_tier = symbol_row.get("coverage_tier") or existing.get("coverage_tier") or "cold"

        if snapshot and snapshot.get("close") is not None:
            price_source = ((snapshot.get("payload") or {}).get("price_source") or ("krx_official" if market == "KR" else "yfinance"))
            state_rows.append(
                {
                    "symbol": symbol,
                    "market": market,
                    "coverage_tier": coverage_tier,
                    "freshness_status": "fresh",
                    "last_attempted_at": now_iso,
                    "last_succeeded_at": now_iso,
                    "last_snapshot_at": _snapshot_datetime_iso(snapshot.get("snapshot_date"), now_utc),
                    "last_price": snapshot.get("close"),
                    "last_price_source": price_source,
                    "last_error_code": None,
                    "last_error_message": None,
                    "consecutive_failures": 0,
                    "updated_at": now_iso,
                }
            )
            continue

        freshness_status = _determine_freshness_status(
            existing.get("last_price"),
            existing.get("last_succeeded_at") or existing.get("last_attempted_at"),
            now_utc=now_utc,
        )
        state_rows.append(
            {
                "symbol": symbol,
                "market": market,
                "coverage_tier": coverage_tier,
                "freshness_status": freshness_status,
                "last_attempted_at": now_iso,
                "last_succeeded_at": existing.get("last_succeeded_at"),
                "last_snapshot_at": existing.get("last_snapshot_at"),
                "last_price": existing.get("last_price"),
                "last_price_source": existing.get("last_price_source"),
                "last_error_code": "snapshot_missing",
                "last_error_message": f"{phase} returned no price row",
                "consecutive_failures": int(existing.get("consecutive_failures") or 0) + 1,
                "updated_at": now_iso,
            }
        )
        failure_logs.append(
            _build_failure_log_row(
                run_id=run_id,
                symbol=symbol,
                market=market,
                phase=phase,
                provider=resolve_kr_price_provider() if market == "KR" else "yfinance",
                error_code="snapshot_missing",
                error_message=f"{phase} returned no price row",
            )
        )

    return state_rows, failure_logs


def _run_snapshot_phase(phase: str, symbol_rows: list[dict], run_id: str, universe_rows: list[dict] | None = None) -> int:
    if not symbol_rows:
        return 0

    existing_state_rows = _load_state_rows()
    snapshot_rows, provider_failures = _fetch_snapshots_for_symbols(symbol_rows, phase)
    if snapshot_rows:
        _upsert_rows("market_snapshot_daily", snapshot_rows, "symbol,snapshot_date")

    state_rows, result_failures = _build_state_updates_for_attempts(
        symbol_rows,
        snapshot_rows,
        existing_state_rows,
        phase=phase,
        run_id=run_id,
    )
    _upsert_state_rows(state_rows)
    _insert_failure_logs(provider_failures + result_failures)

    if snapshot_rows:
        _rebuild_summary_from_sources(universe_rows=universe_rows, current_snapshot_rows=snapshot_rows)

    return len(snapshot_rows)


def run_kr_hot(run_id: str, universe_rows: list[dict] | None = None) -> int:
    symbol_rows = _resolve_phase_symbol_rows(market="KR", tier="hot", universe_rows=universe_rows)
    return _run_snapshot_phase("kr-hot", symbol_rows, run_id, universe_rows=universe_rows)


def run_us_hot(run_id: str, universe_rows: list[dict] | None = None) -> int:
    symbol_rows = _resolve_phase_symbol_rows(market="US", tier="hot", universe_rows=universe_rows)
    return _run_snapshot_phase("us-hot", symbol_rows, run_id, universe_rows=universe_rows)


def _current_warm_bucket(now_utc: datetime | None = None) -> int:
    now_utc = now_utc or datetime.now(timezone.utc)
    return (now_utc.hour // 2) % WARM_BUCKET_COUNT


def run_warm_rotate(run_id: str, universe_rows: list[dict] | None = None, bucket: int | None = None) -> int:
    target_bucket = _current_warm_bucket() if bucket is None else bucket
    symbol_rows = _resolve_phase_symbol_rows(tier="warm", bucket=target_bucket, universe_rows=universe_rows)
    return _run_snapshot_phase("warm-rotate", symbol_rows, run_id, universe_rows=universe_rows)


def run_exact_worker(run_id: str) -> int:
    requests = [row for row in _load_queued_refresh_requests(limit=EXACT_WORKER_BATCH_SIZE) if row.get("status") == "queued"]
    if not requests:
        return 0

    universe_lookup = {(row["symbol"], row["market"]): row for row in _load_universe_rows()}
    symbol_rows: list[dict] = []
    for request in requests:
        symbol = request["symbol"]
        market = request.get("market")
        if market is None:
            matched = next((row for key, row in universe_lookup.items() if key[0] == symbol), None)
            market = matched.get("market") if matched else None
        if not market:
            _mark_refresh_request_status(symbol, "failed", "market_not_found")
            continue
        _mark_refresh_request_status(symbol, "running")
        symbol_rows.append(
            universe_lookup.get((symbol, market))
            or {"symbol": symbol, "market": market, "coverage_tier": "cold"}
        )

    if not symbol_rows:
        return 0

    snapshot_rows, _ = _fetch_snapshots_for_symbols(symbol_rows, "exact-worker")
    result_count = _run_snapshot_phase("exact-worker", symbol_rows, run_id)
    snapshot_symbols = {row["symbol"] for row in snapshot_rows}
    for row in symbol_rows:
        if row["symbol"] in snapshot_symbols:
            _mark_refresh_request_status(row["symbol"], "done")
        else:
            _mark_refresh_request_status(row["symbol"], "failed", "snapshot_missing")
    return result_count


def _is_kr_market_window(now_utc: datetime) -> bool:
    current = now_utc.astimezone(KST)
    if current.weekday() >= 5:
        return False
    current_minutes = current.hour * 60 + current.minute
    return 9 * 60 <= current_minutes <= 15 * 60 + 30


def _is_us_market_window(now_utc: datetime) -> bool:
    current = now_utc.astimezone(EST)
    if current.weekday() >= 5:
        return False
    current_minutes = current.hour * 60 + current.minute
    return 9 * 60 + 30 <= current_minutes <= 16 * 60


def _resolve_scheduled_phases(now_utc: datetime | None = None) -> list[str]:
    now_utc = now_utc or datetime.now(timezone.utc)
    phases: list[str] = []

    if now_utc.minute == 0 and now_utc.hour == 0:
        phases.append("universe-sync")
    if now_utc.minute == 0 and now_utc.hour % 2 == 0:
        phases.append("warm-rotate")
    if _is_kr_market_window(now_utc):
        phases.append("kr-hot")
    if _is_us_market_window(now_utc):
        phases.append("us-hot")
    return phases


def _create_run_id(prefix: str = "refresh") -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def refresh_all() -> None:
    _clear_broken_proxy_env()
    run_id = _create_run_id("all")
    universe_rows = run_universe_sync(run_id)
    run_kr_hot(run_id, universe_rows=universe_rows)
    run_us_hot(run_id, universe_rows=universe_rows)
    run_warm_rotate(run_id, universe_rows=universe_rows)

    if universe_rows:
        first_symbol = next((row["symbol"] for row in universe_rows if row.get("market") == "KR"), None)
        if first_symbol:
            try:
                payload = collect_kr_fundamentals(first_symbol.replace(".KS", ""), "2025")
                upsert_json("fundamentals_cache", {"symbol": first_symbol, "payload": payload}, "symbol")
            except Exception:
                pass


def run_scheduled() -> None:
    _clear_broken_proxy_env()
    run_id = _create_run_id("scheduled")
    phases = _resolve_scheduled_phases()
    universe_rows: list[dict] | None = None

    if "universe-sync" in phases:
        universe_rows = run_universe_sync(run_id)
    if "kr-hot" in phases:
        run_kr_hot(run_id, universe_rows=universe_rows)
    if "us-hot" in phases:
        run_us_hot(run_id, universe_rows=universe_rows)
    if "warm-rotate" in phases:
        run_warm_rotate(run_id, universe_rows=universe_rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=["all", "scheduled", "universe-sync", "kr-hot", "us-hot", "warm-rotate", "exact-worker", "summary"],
        default="all",
    )
    args = parser.parse_args()

    if args.phase == "all":
        refresh_all()
    elif args.phase == "scheduled":
        run_scheduled()
    elif args.phase == "universe-sync":
        _clear_broken_proxy_env()
        run_universe_sync(_create_run_id("universe"))
    elif args.phase == "kr-hot":
        _clear_broken_proxy_env()
        run_kr_hot(_create_run_id("kr-hot"))
    elif args.phase == "us-hot":
        _clear_broken_proxy_env()
        run_us_hot(_create_run_id("us-hot"))
    elif args.phase == "warm-rotate":
        _clear_broken_proxy_env()
        run_warm_rotate(_create_run_id("warm"))
    elif args.phase == "exact-worker":
        _clear_broken_proxy_env()
        run_exact_worker(_create_run_id("exact"))
    elif args.phase == "summary":
        _clear_broken_proxy_env()
        _rebuild_summary_from_sources()
