from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from core.supabase_client import get_supabase

_CACHE_VALID_HOURS = 25


def _is_fresh(fetched_at: str | None) -> bool:
    if not fetched_at:
        return False
    value = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) - value < timedelta(hours=_CACHE_VALID_HOURS)


def read_json(table: str, key_field: str, key_value: str, payload_field: str = "payload") -> dict[str, Any] | None:
    try:
        result = (
            get_supabase()
            .table(table)
            .select(f"{payload_field}, fetched_at")
            .eq(key_field, key_value)
            .single()
            .execute()
        )
        row = result.data
        if row and _is_fresh(row.get("fetched_at")):
            return row.get(payload_field)
    except Exception:
        return None
    return None


def upsert_json(table: str, row: dict[str, Any], conflict: str) -> None:
    payload = {**row, "fetched_at": datetime.now(timezone.utc).isoformat()}
    get_supabase().table(table).upsert(payload, on_conflict=conflict).execute()
