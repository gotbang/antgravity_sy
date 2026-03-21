from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CachePolicy:
    allow_live_price_fallback: bool = True
    allow_live_fundamentals_fallback: bool = False
    allow_live_summary_fallback: bool = False


DEFAULT_CACHE_POLICY = CachePolicy()


def should_live_fetch(kind: str) -> bool:
    if kind == "price":
        return DEFAULT_CACHE_POLICY.allow_live_price_fallback
    if kind in {"fundamentals", "summary", "dart", "ai"}:
        return False
    return False
