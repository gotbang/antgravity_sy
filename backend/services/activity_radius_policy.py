from __future__ import annotations

from typing import Any

DEFAULT_RADIUS_PCT = 5.0
MIN_RADIUS_PCT = 1.5
MAX_RADIUS_PCT = 6.0


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _normalize_number(value: Any, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if number != number:
        return fallback
    return number


def build_safe_activity_radius(
    snapshot: dict[str, Any],
    market_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fear_greed = _normalize_number((market_summary or {}).get("fearGreedIndex"), 50.0)
    change_pct = abs(_normalize_number(snapshot.get("change_pct"), 0.0))
    volume = snapshot.get("volume")
    market = snapshot.get("market")

    radius = DEFAULT_RADIUS_PCT

    if fear_greed <= 30 or fear_greed >= 70:
        radius -= 1.5
    elif fear_greed <= 40 or fear_greed >= 60:
        radius -= 0.8
    else:
        radius += 0.2

    if change_pct >= 7:
        radius -= 2.0
    elif change_pct >= 4:
        radius -= 1.2
    elif change_pct >= 2:
        radius -= 0.5
    else:
        radius += 0.3

    if volume is not None:
        volume_number = _normalize_number(volume, 0.0)
        if market == "US" and volume_number < 50_000:
            radius -= 0.5
        elif market == "KR" and volume_number < 100_000:
            radius -= 0.5

    radius = round(_clamp(radius, MIN_RADIUS_PCT, MAX_RADIUS_PCT), 1)

    if radius >= 4.5:
        level = "safe"
        label = "안전 구역이 넓어. 욕심내지 말고 천천히 움직여."
    elif radius >= 3.0:
        level = "caution"
        label = "반경이 줄었어. 분할 진입과 짧은 탐색이 유리해."
    else:
        level = "danger"
        label = "반경이 아주 좁아. 무리한 접근은 피하는 게 좋아."

    return {
        "safe_activity_radius_pct": radius,
        "safe_activity_level": level,
        "safe_activity_label": label,
    }
