import { describe, expect, it, vi } from "vitest";

import {
  DIRECT_READ_FRESHNESS_HOURS,
  adaptHomeSummaryRow,
  adaptStockDetailRow,
  isFreshEnough,
  sortSearchRows
} from "../lib/supabase-adapters.js";

describe("supabase direct adapters", () => {
  it("maps home summary rows into the current UI shape", () => {
    const result = adaptHomeSummaryRow({
      market_mood: "탐욕",
      fear_greed_index: 72,
      advancers: 10,
      decliners: 4,
      positive_ratio: 70,
      negative_ratio: 30,
      ai_summary: "상승 우위",
      updated_at: "2026-03-22T00:00:00.000Z"
    });

    expect(result.marketMood).toBe("탐욕");
    expect(result.fearGreedIndex).toBe(72);
    expect(result.sentimentMix.positive).toBe(70);
  });

  it("maps stock detail rows while keeping null-safe fields", () => {
    const result = adaptStockDetailRow({
      symbol: "AAPL",
      name: "Apple Inc.",
      market: "US",
      price: 200.5,
      change_pct: 1.2,
      market_cap: null,
      volume: 1000,
      per: null,
      pbr: null,
      snapshot_date: "2026-03-21",
      summary: null,
      price_source: "snapshot"
    });

    expect(result.symbol).toBe("AAPL");
    expect(result.change_pct).toBe(1.2);
    expect(result.price_source).toBe("snapshot");
  });

  it("treats timestamps inside the freshness window as valid", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-03-22T20:00:00.000Z"));

    expect(isFreshEnough("2026-03-22T01:00:00.000Z", DIRECT_READ_FRESHNESS_HOURS)).toBe(true);
    expect(isFreshEnough("2026-03-21T20:00:00.000Z", DIRECT_READ_FRESHNESS_HOURS)).toBe(false);
  });

  it("sorts search rows by exact match, prefix, then contains", () => {
    const result = sortSearchRows(
      [
        { symbol: "005930.KS", name: "삼성전자", market: "KR", search_text: "005930.ks 삼성전자" },
        { symbol: "AAPL", name: "Apple Inc.", market: "US", search_text: "aapl apple inc." },
        { symbol: "032830.KS", name: "삼성생명", market: "KR", search_text: "032830.ks 삼성생명" }
      ],
      "삼성"
    );

    expect(result[0]?.name).toBe("삼성생명");
    expect(result[1]?.name).toBe("삼성전자");
  });
});
