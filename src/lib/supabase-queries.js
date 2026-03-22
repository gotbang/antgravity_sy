import { adaptHomeSummaryRow, adaptStockDetailRow, sortSearchRows } from "./supabase-adapters.js";
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

  const { data, error } = await client
    .from("v_stock_search")
    .select("symbol,name,market,sector,industry,search_text")
    .ilike("search_text", `%${safeQuery}%`)
    .limit(8);

  if (error) {
    throw error;
  }

  return sortSearchRows(data ?? [], safeQuery);
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
