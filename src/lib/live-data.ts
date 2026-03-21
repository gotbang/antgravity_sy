import type { MarketSummaryResponse } from './apiClient';

export function toHomeCardData(summary: MarketSummaryResponse) {
  return {
    mood: summary.marketMood,
    fearGreed: summary.fearGreedIndex,
    gainers: summary.advancers,
    losers: summary.decliners,
    aiSummary: summary.aiSummary,
  };
}
