import { adaptHomeSummaryRow, adaptSearchRow, adaptStockDetailRow, sortSearchRows } from "./supabase-adapters.js";
import { getBrowserSupabase } from "./supabase-browser.js";

export async function fetchHomeSummaryDirect(client = getBrowserSupabase()) {
  const { data, error } = await client
    .from("v_home_summary")
    .select("*")
    .limit(1)
    .maybeSingle();

  if (error) {
    throw error;
  }

  return data ? adaptHomeSummaryRow(data) : null;
}

export async function searchStocksDirect(query, client = getBrowserSupabase()) {
  const safeQuery = query.trim().toLowerCase();
  if (!safeQuery) {
    return [];
  }

  const runSelect = (projection) =>
    client
      .from("v_stock_search")
      .select(projection)
      .ilike("search_text", `%${safeQuery}%`)
      .limit(8);

  let response = await runSelect("symbol,name,market,sector,industry,search_text,price_status,price_source,coverage_tier,freshness_status,last_succeeded_at,last_snapshot_at");
  if (response.error) {
    response = await runSelect("symbol,name,market,sector,industry,search_text");
  }

  if (response.error) {
    throw response.error;
  }

  const sorted = sortSearchRows((response.data ?? []).map(adaptSearchRow), safeQuery);
  const available = sorted.filter((item) => item.price_status !== "missing");
  return (available.length ? available : sorted).slice(0, 8);
}

export async function fetchStockDetailDirect(symbol, client = getBrowserSupabase()) {
  const { data, error } = await client
    .from("v_stock_detail_latest")
    .select("*")
    .eq("symbol", symbol)
    .limit(1)
    .maybeSingle();

  if (error) {
    throw error;
  }

  return data ? adaptStockDetailRow(data) : null;
}
