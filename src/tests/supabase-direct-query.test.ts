import { describe, expect, it } from "vitest";

import {
  fetchHomeSummaryDirect,
  fetchStockDetailDirect,
  searchStocksDirect
} from "../lib/supabase-queries.js";

function createSingleClient(expectedTable: string, payload: unknown) {
  const operations: Array<[string, unknown]> = [];
  const builder = {
    select(value: string) {
      operations.push(["select", value]);
      return this;
    },
    limit(value: number) {
      operations.push(["limit", value]);
      return this;
    },
    eq(value: string, match: string) {
      operations.push(["eq", `${value}:${match}`]);
      return this;
    },
    async maybeSingle() {
      return { data: payload, error: null };
    }
  };

  return {
    operations,
    from(table: string) {
      operations.push(["from", table]);
      expect(table).toBe(expectedTable);
      return builder;
    }
  };
}

function createSearchClient(rows: unknown[]) {
  const operations: Array<[string, unknown]> = [];
  const builder = {
    select(value: string) {
      operations.push(["select", value]);
      return this;
    },
    ilike(column: string, pattern: string) {
      operations.push(["ilike", `${column}:${pattern}`]);
      return this;
    },
    async limit(value: number) {
      operations.push(["limit", value]);
      return { data: rows, error: null };
    }
  };

  return {
    operations,
    from(table: string) {
      operations.push(["from", table]);
      expect(table).toBe("v_stock_search");
      return builder;
    }
  };
}

describe("supabase direct queries", () => {
  it("reads the home summary from the public summary view", async () => {
    const client = createSingleClient("v_home_summary", {
      market_mood: "중립",
      fear_greed_index: 50,
      advancers: 1,
      decliners: 1,
      positive_ratio: 50,
      negative_ratio: 50,
      ai_summary: "중립"
    });

    const result = await fetchHomeSummaryDirect(client as never);

    expect(client.operations).toEqual([
      ["from", "v_home_summary"],
      ["select", "*"],
      ["limit", 1]
    ]);
    expect(result?.marketMood).toBe("중립");
  });

  it("reads the latest stock detail from the public detail view", async () => {
    const client = createSingleClient("v_stock_detail_latest", {
      symbol: "AAPL",
      name: "Apple Inc.",
      market: "US",
      price: 200,
      change_pct: 1.1,
      summary: "요약"
    });

    const result = await fetchStockDetailDirect("AAPL", client as never);

    expect(client.operations).toEqual([
      ["from", "v_stock_detail_latest"],
      ["select", "*"],
      ["eq", "symbol:AAPL"],
      ["limit", 1]
    ]);
    expect(result?.symbol).toBe("AAPL");
  });

  it("queries the search view and keeps only the capped direct-read results", async () => {
    const client = createSearchClient([
      { symbol: "032830.KS", name: "삼성생명", market: "KR", search_text: "032830.ks 삼성생명" },
      { symbol: "005930.KS", name: "삼성전자", market: "KR", search_text: "005930.ks 삼성전자" }
    ]);

    const result = await searchStocksDirect("삼성", client as never);

    expect(client.operations).toEqual([
      ["from", "v_stock_search"],
      ["select", "symbol,name,market,sector,industry,search_text"],
      ["ilike", "search_text:%삼성%"],
      ["limit", 8]
    ]);
    expect(result).toHaveLength(2);
  });
});
