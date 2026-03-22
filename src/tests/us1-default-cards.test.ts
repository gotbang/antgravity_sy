import { beforeEach, describe, expect, it } from "vitest";

import { loadStockCard } from "../lib/direct-read-runtime.js";

describe("US1 default cards direct-read", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <h3 id="stock-card-1-name"></h3>
      <p id="stock-card-1-symbol"></p>
      <p id="stock-card-1-price"></p>
      <p id="stock-card-1-change" class="text-[#A45B3E]"></p>
      <h3 id="stock-card-2-name"></h3>
      <p id="stock-card-2-symbol"></p>
      <p id="stock-card-2-price"></p>
      <p id="stock-card-2-change" class="text-[#A45B3E]"></p>
    `;
  });

  it("renders AAPL and TSLA cards from v_stock_detail_latest-shaped data", async () => {
    const details = new Map([
      ["AAPL", {
        symbol: "AAPL",
        name: "Apple Inc.",
        market: "US",
        price: 201.12,
        change_pct: 1.3,
        market_cap: null,
        volume: null,
        per: null,
        pbr: null,
        snapshot_date: null,
        summary: null,
        price_source: "snapshot"
      }],
      ["TSLA", {
        symbol: "TSLA",
        name: "Tesla, Inc.",
        market: "US",
        price: 189.55,
        change_pct: -2.4,
        market_cap: null,
        volume: null,
        per: null,
        pbr: null,
        snapshot_date: null,
        summary: null,
        price_source: "snapshot"
      }]
    ]);

    const fetchStockDetail = async (symbol: string) => details.get(symbol) ?? null;

    await loadStockCard({ symbol: "AAPL", index: 1, fetchStockDetail });
    await loadStockCard({ symbol: "TSLA", index: 2, fetchStockDetail });

    expect(document.getElementById("stock-card-1-name")?.textContent).toBe("Apple Inc.");
    expect(document.getElementById("stock-card-1-symbol")?.textContent).toBe("AAPL");
    expect(document.getElementById("stock-card-1-price")?.textContent).toContain("$");
    expect(document.getElementById("stock-card-2-name")?.textContent).toBe("Tesla, Inc.");
    expect(document.getElementById("stock-card-2-symbol")?.textContent).toBe("TSLA");
    expect(document.getElementById("stock-card-2-change")?.textContent).toBe("-2.4%");
  });
});
