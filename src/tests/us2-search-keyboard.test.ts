import { beforeEach, describe, expect, it, vi } from "vitest";

import { createSearchController } from "../lib/direct-read-runtime.js";

describe("US2 search keyboard and selection", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    document.body.innerHTML = `
      <input id="stock-search-input" />
      <div id="stock-search-results" class="hidden">
        <p id="stock-search-results-status" class="hidden"></p>
        <div id="stock-search-results-list"></div>
      </div>
      <h3 id="stock-card-1-name"></h3>
      <p id="stock-card-1-symbol"></p>
      <p id="stock-card-1-price"></p>
      <p id="stock-card-1-change"></p>
    `;
  });

  it("supports keyboard selection and refreshes card 1 through direct detail query", async () => {
    const searchStocks = vi.fn(async () => [
      { symbol: "005930.KS", name: "삼성전자", market: "KR" },
      { symbol: "000660.KS", name: "SK하이닉스", market: "KR" }
    ]);
    const fetchStockDetail = vi.fn(async (symbol) => ({
      symbol,
      name: symbol === "000660.KS" ? "SK하이닉스" : "삼성전자",
      market: "KR",
      price: 150000,
      change_pct: 1.5,
      market_cap: null,
      volume: null,
      per: null,
      pbr: null,
      snapshot_date: null,
      summary: null,
      price_source: "snapshot"
    }));
    const onToast = vi.fn();

    const controller = createSearchController({
      searchStocks,
      fetchStockDetail,
      onToast,
      debounceMs: 200
    });
    controller.bind();

    const input = document.getElementById("stock-search-input") as HTMLInputElement;
    input.value = "하이닉스";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await vi.advanceTimersByTimeAsync(200);

    input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    await Promise.resolve();
    await Promise.resolve();

    expect(fetchStockDetail).toHaveBeenCalledWith("000660.KS");
    expect(document.getElementById("stock-card-1-symbol")?.textContent).toBe("000660.KS");
    expect(onToast).toHaveBeenCalled();
    expect(document.getElementById("stock-search-results")?.classList.contains("hidden")).toBe(true);
  });
});
