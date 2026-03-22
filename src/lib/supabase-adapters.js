export const DIRECT_READ_FRESHNESS_HOURS = 20;

function parseTimestamp(value) {
  const time = new Date(value).getTime();
  return Number.isFinite(time) ? time : NaN;
}

export function isFreshEnough(updatedAt, maxAgeHours = DIRECT_READ_FRESHNESS_HOURS) {
  const updatedAtMs = parseTimestamp(updatedAt);
  if (Number.isNaN(updatedAtMs)) {
    return false;
  }

  const maxAgeMs = maxAgeHours * 60 * 60 * 1000;
  return Date.now() - updatedAtMs <= maxAgeMs;
}

export function adaptHomeSummaryRow(row) {
  return {
    marketMood: row.market_mood,
    fearGreedIndex: Number(row.fear_greed_index ?? 50),
    advancers: Number(row.advancers ?? 0),
    decliners: Number(row.decliners ?? 0),
    sentimentMix: {
      positive: Number(row.positive_ratio ?? 0),
      negative: Number(row.negative_ratio ?? 0)
    },
    aiSummary: row.ai_summary ?? "시장 요약 데이터가 아직 없어.",
    updatedAt: row.updated_at
  };
}

export function adaptStockDetailRow(row) {
  return {
    symbol: row.symbol,
    name: row.name ?? row.symbol,
    market: row.market,
    price: row.price ?? null,
    change_pct: row.change_pct ?? null,
    market_cap: row.market_cap ?? null,
    volume: row.volume ?? null,
    per: row.per ?? null,
    pbr: row.pbr ?? null,
    snapshot_date: row.snapshot_date ?? null,
    summary: row.summary ?? null,
    price_source: row.price_source ?? null
  };
}

export function scoreSearchRow(row, query) {
  const safeQuery = query.trim().toLowerCase();
  const symbol = String(row.symbol ?? "").toLowerCase();
  const name = String(row.name ?? "").toLowerCase();
  const searchText = String(row.search_text ?? "").toLowerCase();

  if (symbol === safeQuery) return 0;
  if (symbol.startsWith(safeQuery)) return 1;
  if (name.startsWith(safeQuery)) return 2;
  if (searchText.includes(safeQuery)) return 3;
  return 4;
}

export function sortSearchRows(rows, query) {
  return [...rows].sort((left, right) => {
    const leftScore = scoreSearchRow(left, query);
    const rightScore = scoreSearchRow(right, query);
    if (leftScore !== rightScore) {
      return leftScore - rightScore;
    }

    const marketCompare = String(left.market ?? "").localeCompare(String(right.market ?? ""));
    if (marketCompare !== 0) {
      return marketCompare;
    }

    return String(left.name ?? "").localeCompare(String(right.name ?? ""));
  });
}
