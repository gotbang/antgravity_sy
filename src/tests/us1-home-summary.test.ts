import { beforeEach, describe, expect, it } from "vitest";

import { loadTodayTab } from "../lib/direct-read-runtime.js";

describe("US1 home summary direct-read", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <span id="today-risk-stage"></span>
      <span id="today-market-mood"></span>
      <p id="today-ai-summary"></p>
      <span id="today-risk-score"></span>
      <p id="today-risk-caption"></p>
      <span id="today-positive"></span>
      <span id="today-neutral"></span>
      <span id="today-negative"></span>
      <div id="today-positive-bar"></div>
      <div id="today-neutral-bar"></div>
      <div id="today-negative-bar"></div>
      <div id="today-risk-bar"></div>
    `;
  });

  it("renders the today tab from v_home_summary-shaped data without legacy fetch", async () => {
    const legacyFetch = globalThis.fetch;
    const fetchHomeSummary = async () => ({
      marketMood: "탐욕",
      fearGreedIndex: 72,
      advancers: 14,
      decliners: 3,
      sentimentMix: {
        positive: 70,
        negative: 15
      },
      aiSummary: "상승 우위",
      updatedAt: "2026-03-22T00:00:00.000Z"
    });

    await loadTodayTab({ fetchHomeSummary });

    expect(document.getElementById("today-risk-stage")?.textContent).toBe("탐욕");
    expect(document.getElementById("today-market-mood")?.textContent).toBe("탐욕");
    expect(document.getElementById("today-risk-score")?.textContent).toBe("72");
    expect(document.getElementById("today-ai-summary")?.textContent).toContain("상승");
    expect(document.getElementById("today-risk-caption")?.textContent).toContain("상승 14개");
    expect(globalThis.fetch).toBe(legacyFetch);
  });

  it("keeps loading-friendly placeholders when summary data is unavailable", async () => {
    const result = await loadTodayTab({
      fetchHomeSummary: async () => null,
    });

    expect(result).toBeNull();
    expect(document.getElementById("today-risk-score")?.textContent).toBe("");
  });
});
