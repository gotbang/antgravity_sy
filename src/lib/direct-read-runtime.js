import { fetchHomeSummaryDirect, fetchStockDetailDirect } from "./supabase-queries.js";

function applyText(element, value) {
  if (element && value !== undefined && value !== null) {
    element.textContent = String(value);
  }
}

function applyPercentBar(element, value) {
  if (!element || value === undefined || value === null) {
    return;
  }

  const safeValue = Math.max(0, Math.min(100, Number(value)));
  element.style.width = `${safeValue}%`;
}

function formatSignedPercent(value) {
  const numberValue = Number(value ?? 0);
  const prefix = numberValue > 0 ? "+" : "";
  return `${prefix}${numberValue.toFixed(1)}%`;
}

export function formatDirectPrice(value, market) {
  const numberValue = Number(value ?? 0);
  if (!Number.isFinite(numberValue) || value === null) {
    return "-";
  }

  const currency = market === "KR" ? "KRW" : "USD";
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(numberValue);
}

export async function loadTodayTab({
  documentRef = document,
  fetchHomeSummary = fetchHomeSummaryDirect
} = {}) {
  const summary = await fetchHomeSummary();
  if (!summary) {
    return null;
  }

  applyText(documentRef.getElementById("today-risk-stage"), summary.marketMood ?? "중립");
  applyText(documentRef.getElementById("today-market-mood"), summary.marketMood ?? "오늘의 예측");
  applyText(documentRef.getElementById("today-ai-summary"), summary.aiSummary ?? "AI 요약 데이터가 없습니다.");
  applyText(documentRef.getElementById("today-risk-score"), summary.fearGreedIndex ?? 50);
  applyText(
    documentRef.getElementById("today-risk-caption"),
    `상승 ${summary.advancers ?? 0}개 / 하락 ${summary.decliners ?? 0}개가 집계됐어.`
  );

  const positive = Number(summary?.sentimentMix?.positive ?? 0);
  const negative = Number(summary?.sentimentMix?.negative ?? 0);
  const neutral = Math.max(0, 100 - positive - negative);

  applyText(documentRef.getElementById("today-positive"), `${positive.toFixed(1)}%`);
  applyText(documentRef.getElementById("today-neutral"), `${neutral.toFixed(1)}%`);
  applyText(documentRef.getElementById("today-negative"), `${negative.toFixed(1)}%`);

  applyPercentBar(documentRef.getElementById("today-positive-bar"), positive);
  applyPercentBar(documentRef.getElementById("today-neutral-bar"), neutral);
  applyPercentBar(documentRef.getElementById("today-negative-bar"), negative);
  applyPercentBar(documentRef.getElementById("today-risk-bar"), summary.fearGreedIndex ?? 50);

  return summary;
}

export async function loadStockCard({
  symbol,
  index,
  documentRef = document,
  fetchStockDetail = fetchStockDetailDirect
}) {
  const detail = await fetchStockDetail(symbol);
  if (!detail) {
    return null;
  }

  applyText(documentRef.getElementById(`stock-card-${index}-name`), detail.name ?? symbol);
  applyText(documentRef.getElementById(`stock-card-${index}-symbol`), detail.symbol ?? symbol);
  applyText(
    documentRef.getElementById(`stock-card-${index}-price`),
    formatDirectPrice(detail.price, detail.market)
  );

  const changeElement = documentRef.getElementById(`stock-card-${index}-change`);
  const changePct = Number(detail.change_pct ?? detail.changePct ?? 0);
  applyText(changeElement, formatSignedPercent(changePct));
  if (changeElement) {
    changeElement.classList.remove("text-[#6AA84F]", "text-[#A45B3E]");
    changeElement.classList.add(changePct >= 0 ? "text-[#6AA84F]" : "text-[#A45B3E]");
  }

  return detail;
}
