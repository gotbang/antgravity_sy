export interface MarketSummaryResponse {
  marketMood: string;
  fearGreedIndex: number;
  advancers: number;
  decliners: number;
  sentimentMix: {
    positive: number;
    negative: number;
  };
  aiSummary: string;
}

export interface TrendingResponse {
  items: Array<Record<string, unknown>>;
}

export async function fetchMarketSummary(): Promise<MarketSummaryResponse> {
  const response = await fetch('/api/market-summary');
  if (!response.ok) throw new Error('market-summary fetch failed');
  return response.json();
}

export async function fetchTrending(): Promise<TrendingResponse> {
  const response = await fetch('/api/market/trending');
  if (!response.ok) throw new Error('trending fetch failed');
  return response.json();
}

export async function fetchStockSearch(q: string): Promise<Record<string, unknown>> {
  const response = await fetch(`/api/stocks/search?q=${encodeURIComponent(q)}`);
  if (!response.ok) throw new Error('stock-search fetch failed');
  return response.json();
}

export async function fetchStockDetail(symbol: string): Promise<Record<string, unknown>> {
  const response = await fetch(`/api/stocks/${encodeURIComponent(symbol)}`);
  if (!response.ok) throw new Error('stock-detail fetch failed');
  return response.json();
}
