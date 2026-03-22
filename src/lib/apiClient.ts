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

// Legacy read helpers remain only for rollback/troubleshooting while the
// browser moves to Supabase direct-read queries.
function resolveApiUrl(path: string): string {
  if (typeof window === 'undefined') {
    return path;
  }

  const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
  const baseOrigin = isLocalHost && window.location.port !== '8000'
    ? 'http://127.0.0.1:8000'
    : window.location.origin;

  return new URL(path, baseOrigin).toString();
}

export async function fetchMarketSummary(): Promise<MarketSummaryResponse> {
  const response = await fetch(resolveApiUrl('/api/market-summary'));
  if (!response.ok) throw new Error('market-summary fetch failed');
  return response.json();
}

export async function fetchTrending(): Promise<TrendingResponse> {
  const response = await fetch(resolveApiUrl('/api/market/trending'));
  if (!response.ok) throw new Error('trending fetch failed');
  return response.json();
}

export async function fetchStockSearch(q: string): Promise<Record<string, unknown>> {
  const response = await fetch(resolveApiUrl(`/api/stocks/search?q=${encodeURIComponent(q)}`));
  if (!response.ok) throw new Error('stock-search fetch failed');
  return response.json();
}

export async function fetchStockDetail(symbol: string): Promise<Record<string, unknown>> {
  const response = await fetch(resolveApiUrl(`/api/stocks/${encodeURIComponent(symbol)}`));
  if (!response.ok) throw new Error('stock-detail fetch failed');
  return response.json();
}
