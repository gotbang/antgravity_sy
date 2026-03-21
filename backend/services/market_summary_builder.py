from __future__ import annotations

from statistics import mean
from typing import Any


def build_market_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    change_values = [item.get("change_pct") for item in items if item.get("change_pct") is not None]
    positive = sum(1 for value in change_values if value > 0)
    negative = sum(1 for value in change_values if value < 0)
    total = len(change_values) or 1
    average_change = mean(change_values) if change_values else 0.0

    fear_greed = max(0, min(100, int(50 + average_change * 8)))
    mood = "중립"
    if fear_greed >= 65:
        mood = "탐욕"
    elif fear_greed <= 35:
        mood = "공포"

    return {
        "marketMood": mood,
        "fearGreedIndex": fear_greed,
        "advancers": positive,
        "decliners": negative,
        "sentimentMix": {
            "positive": round(positive / total * 100, 1),
            "negative": round(negative / total * 100, 1),
        },
        "aiSummary": f"현재 시장은 {mood} 구간으로 해석되며, 상승 종목 {positive}개 / 하락 종목 {negative}개가 집계됐다.",
    }
