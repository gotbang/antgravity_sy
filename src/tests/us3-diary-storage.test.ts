import { beforeEach, describe, expect, it, vi } from "vitest";

import { createDiaryController } from "../lib/direct-read-runtime.js";

describe("US3 diary storage", () => {
  beforeEach(() => {
    localStorage.clear();
    document.body.innerHTML = `
      <div>
        <label class="mood-card selected" data-emoji="🍯" data-label="달달해">
          <input class="mood-card-input" type="radio" name="diary-mood" value="달달해" checked />
          <span>달달해</span>
        </label>
        <label class="mood-card" data-emoji="💧" data-label="물방울">
          <input class="mood-card-input" type="radio" name="diary-mood" value="물방울" />
          <span>물방울</span>
        </label>
      </div>
      <label for="diary-entry-input">생존 일기 내용</label>
      <textarea id="diary-entry-input"></textarea>
      <button id="diary-save-button" type="button">저장하기</button>
      <p id="diary-history-empty" class="hidden">비어 있음</p>
      <div id="diary-history-list"></div>
    `;
  });

  it("saves a diary entry to localStorage and renders it", () => {
    const onToast = vi.fn();
    const controller = createDiaryController({
      onToast,
      now: () => new Date("2026-03-22T09:00:00+09:00"),
    });

    controller.bind();
    const textarea = document.getElementById("diary-entry-input") as HTMLTextAreaElement;
    textarea.value = "오늘은 시장 바람이 잔잔했어.";

    document.getElementById("diary-save-button")?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(controller.getEntries()).toHaveLength(1);
    expect(controller.getEntries()[0].content).toBe("오늘은 시장 바람이 잔잔했어.");
    expect(controller.getEntries()[0].moodEmoji).toBe("🍯");
    expect(document.getElementById("diary-history-list")?.textContent).toContain("오늘은 시장 바람이 잔잔했어.");
    expect(localStorage.getItem("antgravity-diary-entries")).toContain("오늘은 시장 바람이 잔잔했어.");
    expect(onToast).toHaveBeenCalledWith("생존 일지를 저장했어.");
  });

  it("deletes a saved diary entry from localStorage and shows empty state again", () => {
    localStorage.setItem("antgravity-diary-entries", JSON.stringify([
      {
        id: "1",
        createdAt: "2026.03.22",
        moodEmoji: "💧",
        moodLabel: "물방울",
        content: "기록 하나",
      },
    ]));
    const onToast = vi.fn();
    const controller = createDiaryController({ onToast });

    controller.bind();
    document.querySelector("[data-diary-delete-id=\"1\"]")?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(controller.getEntries()).toHaveLength(0);
    expect(localStorage.getItem("antgravity-diary-entries")).toBe("[]");
    expect(document.getElementById("diary-history-empty")?.classList.contains("hidden")).toBe(false);
    expect(onToast).toHaveBeenCalledWith("기록을 삭제했어.");
  });

  it("renders diary content safely without injecting HTML from storage", () => {
    localStorage.setItem("antgravity-diary-entries", JSON.stringify([
      {
        id: "1",
        createdAt: "2026.03.22",
        moodEmoji: "💧",
        moodLabel: "<script>alert(1)</script>",
        content: "<img src=x onerror=alert(1)>",
      },
    ]));
    const controller = createDiaryController({ onToast: vi.fn() });

    controller.bind();

    expect(document.querySelector("#diary-history-list img")).toBeNull();
    expect(document.querySelector("#diary-history-list script")).toBeNull();
    expect(document.getElementById("diary-history-list")?.textContent).toContain("<img src=x onerror=alert(1)>");
    expect(document.getElementById("diary-history-list")?.textContent).toContain("<script>alert(1)</script>");
    expect(controller.getEntries()).toHaveLength(1);
  });
});
