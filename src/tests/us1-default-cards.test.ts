import { beforeEach, describe, expect, it } from "vitest";

import { loadStockCard } from "../lib/direct-read-runtime.js";

describe("US1 default cards direct-read", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <h3 id="stock-card-1-name"></h3>
      <p id="stock-card-1-symbol"></p>
      <p id="stock-card-1-price"></p>
      <p id="stock-card-1-change" class="text-[#A45B3E]"></p>
      <p id="stock-card-1-price-status"></p>
      <span id="stock-card-1-radius-value"></span>
      <span id="stock-card-1-radius-badge"></span>
      <p id="stock-card-1-radius-caption"></p>
      <div id="stock-card-1-radius-bar"></div>
    `;
  });

  it("renders the single default card from v_stock_detail_latest-shaped data", async () => {
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
        price_status: "live",
        price_source: "snapshot",
        safe_activity_radius_pct: 4.4,
        safe_activity_level: "caution",
        safe_activity_label: "반경이 줄었어."
      }]
    ]);

    const fetchStockDetail = async (symbol: string) => details.get(symbol) ?? null;

    await loadStockCard({ symbol: "AAPL", index: 1, fetchStockDetail });

    expect(document.getElementById("stock-card-1-name")?.textContent).toBe("Apple Inc.");
    expect(document.getElementById("stock-card-1-symbol")?.textContent).toBe("AAPL");
    expect(document.getElementById("stock-card-1-price")?.textContent).toContain("$");
    expect(document.getElementById("stock-card-1-radius-value")?.textContent).toBe("±4.4%");
    expect(document.getElementById("stock-card-1-radius-badge")?.textContent).toBe("주의");
    expect(document.getElementById("stock-card-1-radius-badge")?.className).toContain("bg-[#FFF2CF]");
  });

  it("renders a friendly missing-price state instead of leaving the card blank", async () => {
    const details = new Map([
      ["MSFT", {
        symbol: "MSFT",
        name: "Microsoft",
        market: "US",
        price: null,
        change_pct: null,
        market_cap: null,
        volume: null,
        per: null,
        pbr: null,
        snapshot_date: null,
        summary: null,
        price_status: "missing",
        price_source: "unavailable",
        safe_activity_radius_pct: 3.0,
        safe_activity_level: "danger",
        safe_activity_label: "반경이 아주 좁아."
      }]
    ]);

    const fetchStockDetail = async (symbol: string) => details.get(symbol) ?? null;

    await loadStockCard({ symbol: "MSFT", index: 1, fetchStockDetail });

    expect(document.getElementById("stock-card-1-price")?.textContent).toBe("가격 준비중");
    expect(document.getElementById("stock-card-1-price-status")?.textContent).toContain("시세 미적재");
    expect(document.getElementById("stock-card-1-change")?.textContent).toBe("변동 미확인");
    expect(document.getElementById("stock-card-1-radius-badge")?.textContent).toBe("고위험");
    expect(document.getElementById("stock-card-1-radius-badge")?.className).toContain("bg-[#F7D8D0]");
  });
});
