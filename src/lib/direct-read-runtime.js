import {
  fetchHomeSummaryDirect,
  fetchStockDetailDirect,
  searchStocksDirect
} from "./supabase-queries.js";

const priceFormatters = {
  KR: new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 2
  }),
  US: new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2
  })
};

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

  const formatter = market === "KR" ? priceFormatters.KR : priceFormatters.US;
  return formatter.format(numberValue);
}

function resolvePriceStatusText(detail) {
  if (detail.price_status === "fallback") {
    return "최근 캐시 가격으로 보여주고 있어.";
  }
  if (detail.price_status === "missing") {
    return "시세 미적재 상태야.";
  }
  return "최신 적재 가격이야.";
}

function resolveActivityLevelText(level) {
  if (level === "safe") {
    return "안전";
  }
  if (level === "danger") {
    return "고위험";
  }
  return "주의";
}

function deriveActivityFallback(detail) {
  const changeRaw = detail.change_pct ?? detail.changePct;
  if (changeRaw === null || changeRaw === undefined) {
    return {
      safe_activity_radius_pct: null,
      safe_activity_level: null,
      safe_activity_label: "활동 반경을 계산할 시세가 아직 없어."
    };
  }

  const changePct = Math.abs(Number(changeRaw));
  let radius = 5.0;
  if (changePct >= 7) {
    radius = 2.0;
  } else if (changePct >= 4) {
    radius = 3.0;
  } else if (changePct >= 2) {
    radius = 4.0;
  } else {
    radius = 5.2;
  }

  if (radius >= 4.5) {
    return {
      safe_activity_radius_pct: radius,
      safe_activity_level: "safe",
      safe_activity_label: "현재 변동성 기준으로는 비교적 넓게 움직일 수 있어."
    };
  }
  if (radius >= 3.0) {
    return {
      safe_activity_radius_pct: radius,
      safe_activity_level: "caution",
      safe_activity_label: "현재 변동성이 있어서 반경을 조금 줄여 보는 게 좋아."
    };
  }
  return {
    safe_activity_radius_pct: radius,
    safe_activity_level: "danger",
    safe_activity_label: "변동성이 커서 활동 반경을 아주 좁게 잡는 게 좋아."
  };
}

function applyActivityBadgeState(element, level) {
  if (!element) {
    return;
  }
  element.classList.remove("bg-[#E6F4DA]", "bg-[#FFF2CF]", "bg-[#F7D8D0]");
  element.classList.remove("text-[#35563B]", "text-[#7A4C00]", "text-[#8C3B2A]");
  if (level === "safe") {
    element.classList.add("bg-[#E6F4DA]", "text-[#35563B]");
    return;
  }
  if (level === "danger") {
    element.classList.add("bg-[#F7D8D0]", "text-[#8C3B2A]");
    return;
  }
  element.classList.add("bg-[#FFF2CF]", "text-[#7A4C00]");
}

function resolveSearchBadgeText(item) {
  if (item.price_status === "fallback") {
    return "캐시";
  }
  if (item.price_status === "missing") {
    return "가격 준비중";
  }
  return "실시간";
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
  const priceElement = documentRef.getElementById(`stock-card-${index}-price`);
  applyText(
    priceElement,
    detail.price_status === "missing"
      ? "가격 준비중"
      : formatDirectPrice(detail.price, detail.market)
  );
  applyText(
    documentRef.getElementById(`stock-card-${index}-price-status`),
    resolvePriceStatusText(detail)
  );

  const changeElement = documentRef.getElementById(`stock-card-${index}-change`);
  const rawChangePct = detail.change_pct ?? detail.changePct;
  if (changeElement) {
    changeElement.classList.remove("text-[#6AA84F]", "text-[#A45B3E]", "text-[#8E715C]");
    if (rawChangePct == null) {
      applyText(changeElement, "변동 미확인");
      changeElement.classList.add("text-[#8E715C]");
    } else {
      const changePct = Number(rawChangePct);
      applyText(changeElement, formatSignedPercent(changePct));
      changeElement.classList.add(changePct >= 0 ? "text-[#6AA84F]" : "text-[#A45B3E]");
    }
  }

  const resolvedActivity = detail.safe_activity_radius_pct == null
    ? deriveActivityFallback(detail)
    : {
        safe_activity_radius_pct: Number(detail.safe_activity_radius_pct),
        safe_activity_level: detail.safe_activity_level,
        safe_activity_label: detail.safe_activity_label,
      };
  const radiusValue = resolvedActivity.safe_activity_radius_pct;
  applyText(
    documentRef.getElementById(`stock-card-${index}-radius-value`),
    radiusValue == null ? "계산중" : `±${radiusValue.toFixed(1)}%`
  );
  const radiusBadge = documentRef.getElementById(`stock-card-${index}-radius-badge`);
  applyText(
    radiusBadge,
    resolvedActivity.safe_activity_level ? resolveActivityLevelText(resolvedActivity.safe_activity_level) : "확인중"
  );
  applyActivityBadgeState(radiusBadge, resolvedActivity.safe_activity_level);
  applyText(
    documentRef.getElementById(`stock-card-${index}-radius-caption`),
    resolvedActivity.safe_activity_label ?? "반경 계산 데이터가 아직 없어."
  );
  applyPercentBar(
    documentRef.getElementById(`stock-card-${index}-radius-bar`),
    radiusValue == null ? 0 : (radiusValue / 6) * 100
  );

  return detail;
}

function getSearchElements(documentRef) {
  return {
    input: documentRef.getElementById("stock-search-input"),
    panel: documentRef.getElementById("stock-search-results"),
    list: documentRef.getElementById("stock-search-results-list"),
    status: documentRef.getElementById("stock-search-results-status")
  };
}

function openSearchPanel(panel) {
  panel?.classList.remove("hidden");
}

function closeSearchPanel(panel, list, status) {
  panel?.classList.add("hidden");
  if (list) {
    list.innerHTML = "";
  }
  if (status) {
    status.textContent = "";
    status.classList.add("hidden");
  }
}

function renderSearchStatus(status, message) {
  if (!status) {
    return;
  }

  status.textContent = message;
  status.classList.remove("hidden");
}

function renderSearchResults({
  items,
  activeIndex,
  list,
  status,
  onSelect
}) {
  if (!list) {
    return;
  }

  list.innerHTML = "";
  if (!items.length) {
    renderSearchStatus(status, "검색 결과가 없어.");
    return;
  }

  status?.classList.add("hidden");

  items.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.symbol = item.symbol;
    button.className = [
      "w-full",
      "rounded-2xl",
      "border-[2px]",
      "px-3",
      "py-3",
      "text-left",
      "transition"
    ].join(" ");
    button.dataset.index = String(index);
    const row = document.createElement("div");
    row.className = "flex items-center justify-between gap-3";

    const left = document.createElement("div");
    const name = document.createElement("p");
    name.className = "text-sm font-extrabold text-[#2F1C12]";
    name.textContent = item.name ?? item.symbol;
    const symbol = document.createElement("p");
    symbol.className = "text-[11px] font-semibold text-[#8E715C]";
    symbol.textContent = item.symbol;
    left.append(name, symbol);

    const right = document.createElement("div");
    right.className = "flex flex-col items-end gap-1";
    const market = document.createElement("span");
    market.className = "status-shell px-2 py-1 text-[10px] font-extrabold";
    market.textContent = item.market ?? "-";
    const badge = document.createElement("span");
    badge.className = "text-[10px] font-bold text-[#8E715C]";
    badge.textContent = resolveSearchBadgeText(item);
    right.append(market, badge);

    row.append(left, right);
    button.appendChild(row);
    button.addEventListener("click", async () => {
      await onSelect(item);
    });
    list.appendChild(button);
  });

  updateSearchActiveState(list, activeIndex);
}

function updateSearchActiveState(list, activeIndex) {
  if (!list) {
    return;
  }

  Array.from(list.querySelectorAll("button")).forEach((button, index) => {
    button.classList.remove("border-[#5E3A23]", "bg-[#FFF4D8]", "border-[#D7C1A6]", "bg-[#FFF9F1]");
    if (index === activeIndex) {
      button.classList.add("border-[#5E3A23]", "bg-[#FFF4D8]");
      return;
    }
    button.classList.add("border-[#D7C1A6]", "bg-[#FFF9F1]");
  });
}

export function createSearchController({
  documentRef = document,
  searchStocks = searchStocksDirect,
  fetchStockDetail = fetchStockDetailDirect,
  onToast = () => {},
  debounceMs = 200
} = {}) {
  const { input, panel, list, status } = getSearchElements(documentRef);
  let items = [];
  let activeIndex = -1;
  let debounceHandle = null;

  async function selectItem(item) {
    await loadStockCard({
      symbol: item.symbol,
      index: 1,
      documentRef,
      fetchStockDetail
    });
    onToast(`${item.name ?? item.symbol} 종목을 찾았어.`);
    closeSearchPanel(panel, list, status);
    activeIndex = -1;
  }

  async function runSearch() {
    const query = input?.value?.trim() ?? "";
    if (!query) {
      items = [];
      activeIndex = -1;
      closeSearchPanel(panel, list, status);
      return;
    }

    openSearchPanel(panel);
    renderSearchStatus(status, "검색 중이야...");

    try {
      items = await searchStocks(query);
      activeIndex = items.length ? 0 : -1;
      renderSearchResults({ items, activeIndex, list, status, onSelect: selectItem });
    } catch (error) {
      console.error("stock search failed", error);
      items = [];
      activeIndex = -1;
      if (list) {
        list.innerHTML = "";
      }
      renderSearchStatus(status, "검색 중 문제가 생겼어. 잠시 후 다시 시도해줘.");
    }
  }

  function scheduleSearch() {
    if (debounceHandle) {
      clearTimeout(debounceHandle);
    }

    debounceHandle = setTimeout(() => {
      debounceHandle = null;
      void runSearch();
    }, debounceMs);
  }

  function rerender() {
    updateSearchActiveState(list, activeIndex);
  }

  async function handleKeydown(event) {
    if (event.key === "ArrowDown" && items.length) {
      event.preventDefault();
      activeIndex = (activeIndex + 1) % items.length;
      rerender();
      return;
    }

    if (event.key === "ArrowUp" && items.length) {
      event.preventDefault();
      activeIndex = activeIndex <= 0 ? items.length - 1 : activeIndex - 1;
      rerender();
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      activeIndex = -1;
      closeSearchPanel(panel, list, status);
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();

      if (!items.length) {
        await runSearch();
        return;
      }

      const item = items[activeIndex] ?? items[0];
      if (item) {
        await selectItem(item);
      }
    }
  }

  return {
    async searchNow() {
      await runSearch();
    },
    getState() {
      return { items, activeIndex };
    },
    bind() {
      if (!input) {
        return;
      }

      input.addEventListener("input", scheduleSearch);
      input.addEventListener("keydown", (event) => {
        void handleKeydown(event);
      });
    }
  };
}

const diaryStorageKey = "antgravity-diary-entries";

function formatDiaryDate(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}.${month}.${day}`;
}

function readDiaryEntries(storage) {
  const raw = storage?.getItem(diaryStorageKey);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeDiaryEntries(storage, entries) {
  storage?.setItem(diaryStorageKey, JSON.stringify(entries));
}

function getDiaryElements(documentRef) {
  return {
    textarea: documentRef.getElementById("diary-entry-input"),
    saveButton: documentRef.getElementById("diary-save-button"),
    list: documentRef.getElementById("diary-history-list"),
    empty: documentRef.getElementById("diary-history-empty"),
  };
}

function getSelectedMood(documentRef) {
  const selectedInput = documentRef.querySelector(".mood-card-input:checked");
  const selected = selectedInput?.closest(".mood-card") ?? documentRef.querySelector(".mood-card.selected");
  return {
    emoji: selected?.dataset.emoji ?? "🍯",
    label: selected?.dataset.label ?? "달달해",
  };
}

function renderDiaryEntries(entries, { list, empty, onDelete }) {
  if (!list) {
    return;
  }

  list.innerHTML = "";

  if (!entries.length) {
    empty?.classList.remove("hidden");
    return;
  }

  empty?.classList.add("hidden");

  entries.forEach((entry) => {
    const wrapper = document.createElement("div");
    wrapper.className = "market-badge p-3";
    const header = document.createElement("div");
    header.className = "flex items-start justify-between gap-3 mb-1";

    const meta = document.createElement("div");
    meta.className = "flex items-center gap-2";
    const emoji = document.createElement("span");
    emoji.className = "text-lg";
    emoji.textContent = entry.moodEmoji;
    const metaText = document.createElement("div");
    metaText.className = "flex flex-col";
    const createdAt = document.createElement("span");
    createdAt.className = "text-xs text-[#8E715C] font-bold";
    createdAt.textContent = entry.createdAt;
    const moodLabel = document.createElement("span");
    moodLabel.className = "text-[11px] text-[#8E715C] font-extrabold";
    moodLabel.textContent = entry.moodLabel;
    metaText.append(createdAt, moodLabel);
    meta.append(emoji, metaText);

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.dataset.diaryDeleteId = entry.id;
    deleteButton.className = "rounded-full border border-[#D7C1A6] bg-[#FFF8EF] px-3 py-1 text-[11px] font-extrabold text-[#8E715C]";
    deleteButton.textContent = "삭제";
    deleteButton.addEventListener("click", () => {
      onDelete(entry.id);
    });

    header.append(meta, deleteButton);

    const content = document.createElement("p");
    content.className = "text-sm text-[#6E4C39] font-diary whitespace-pre-wrap";
    content.textContent = entry.content;

    wrapper.append(header, content);
    list.appendChild(wrapper);
  });
}

export function createDiaryController({
  documentRef = document,
  storage = globalThis.localStorage,
  onToast = () => {},
  now = () => new Date(),
} = {}) {
  const elements = getDiaryElements(documentRef);
  let entries = readDiaryEntries(storage);

  const rerender = () => {
    renderDiaryEntries(entries, {
      list: elements.list,
      empty: elements.empty,
      onDelete: deleteEntry,
    });
  };

  function saveEntry() {
    const content = elements.textarea?.value?.trim() ?? "";
    if (!content) {
      onToast("일지를 먼저 적어줘.");
      elements.textarea?.focus();
      return;
    }

    const mood = getSelectedMood(documentRef);
    const entry = {
      id: `${now().getTime()}`,
      createdAt: formatDiaryDate(now()),
      moodEmoji: mood.emoji,
      moodLabel: mood.label,
      content,
    };

    entries = [entry, ...entries];
    writeDiaryEntries(storage, entries);
    rerender();

    if (elements.textarea) {
      elements.textarea.value = "";
    }
    onToast("생존 일지를 저장했어.");
  }

  function deleteEntry(id) {
    entries = entries.filter((entry) => entry.id !== id);
    writeDiaryEntries(storage, entries);
    rerender();
    onToast("기록을 삭제했어.");
  }

  return {
    bind() {
      rerender();
      elements.saveButton?.addEventListener("click", saveEntry);
    },
    saveNow() {
      saveEntry();
    },
    getEntries() {
      return [...entries];
    },
  };
}
