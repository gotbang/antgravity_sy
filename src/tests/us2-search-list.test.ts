import { beforeEach, describe, expect, it, vi } from "vitest";

import { createSearchController } from "../lib/direct-read-runtime.js";

describe("US2 search list direct-read", () => {
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

  it("renders capped search results from v_stock_search-shaped data", async () => {
    const searchStocks = vi.fn(async () =>
      Array.from({ length: 10 }, (_, index) => ({
        symbol: `SYM${index}`,
        name: `종목${index}`,
        market: index % 2 === 0 ? "KR" : "US"
      })).slice(0, 8)
    );

    const controller = createSearchController({
      searchStocks,
      fetchStockDetail: vi.fn(),
      onToast: vi.fn(),
      debounceMs: 200
    });
    controller.bind();

    const input = document.getElementById("stock-search-input") as HTMLInputElement;
    input.value = "삼성";
    input.dispatchEvent(new Event("input", { bubbles: true }));

    await vi.advanceTimersByTimeAsync(200);

    expect(searchStocks).toHaveBeenCalledWith("삼성");
    expect(document.getElementById("stock-search-results")?.classList.contains("hidden")).toBe(false);
    expect(document.querySelectorAll("#stock-search-results-list button")).toHaveLength(8);
  });
});
