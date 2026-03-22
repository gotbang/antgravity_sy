# AntGravity Supabase direct-read Tasks

## 작성시각
2026-03-22 16:20:06 KST

## 문서 목적
이 문서는 direct-read 전환 완료 이후 이어진 후속 개선 작업까지 포함한 실행 결과를 기록한다. 이번 갱신에서는 가격 공백 해소, 활동반경 실데이터화, 문서 5종 동기화를 추가 완료 작업으로 반영한다.

## 현재 완료 상태
- 완료 태스크 수: `72`
- 미완료 태스크 수: `0`
- 구현 기준
  - direct-read 공개 뷰 3개 사용
  - 오늘 탭 동작
  - 단일 종목 카드 동작
  - 검색 결과 리스트/선택 동작
  - 가격 상태 UI
  - 활동반경 실데이터화
  - 검색 결과 가격 배지
  - 대표 US fallback 적재
  - 활동반경 표현 강화
  - freshness `20시간`
  - rollback-only FastAPI read path 유지

## User Story 결과 요약

### US1 (P1)
오늘 탭과 기본 단일 카드가 Supabase direct-read 조회로 동작한다.

실행 결과:
- `v_home_summary` 렌더 성공
- 기본 카드 `AAPL` 렌더 성공
- 오늘 탭 placeholder 숫자 제거

### US2 (P1)
검색 결과 리스트와 종목 선택이 Supabase direct-read 조회로 동작한다.

실행 결과:
- 최대 8건 검색 리스트 노출
- 클릭/Enter/방향키/Escape 동작
- 선택 후 카드 1 갱신
- 가격이 없는 종목도 카드 빈칸 대신 상태 문구 표시

### US3 (P2)
공개 뷰, RLS, 적재 품질 게이트가 direct-read 구조를 지지한다.

실행 결과:
- 공개 뷰 계약 테스트 통과
- freshness `20시간` 계약 통과
- empty summary overwrite 방지 반영
- 활동반경 계산 정책 반영

### US4 (P3)
컷오버, 레거시, 롤백, 문서/검증 체계가 갖춰진다.

실행 결과:
- rollback-only 문맥 문서화
- 가격 상태와 활동반경 정책 문서 5종 동기화

### US5 (P1)
검색 전에 가격 준비 상태를 안다.

실행 결과:
- 검색 결과에 `실시간`, `캐시`, `가격 준비중` 배지 노출
- 검색 전부터 선택 기대치를 조정 가능

### US6 (P1)
대표 US 종목 가격 공백을 더 줄인다.

실행 결과:
- `AAPL`, `TSLA`에 Yahoo chart fallback 경로 추가
- 대표 종목 quality gate가 `missing` 회귀를 더 엄격히 잡음

### US7 (P2)
활동반경 근거를 더 신뢰할 수 있다.

실행 결과:
- 활동반경 라벨 테스트 추가
- 활동반경 배지 시각 차이 강화
- quickstart/research 후속 범위 동기화

## 후속 개선 태스크

### Phase 8. Price Status & Safe Radius
- [X] T046 Extend `v_stock_detail_latest` contract with `price_status`, `price_source`, and safe activity fields
- [X] T047 Persist fallback price/status/activity payload during batch refresh
- [X] T048 Merge previous snapshot values when current batch rows are partially empty
- [X] T049 Render missing-price state in the single stock card without leaving blanks
- [X] T050 Replace fixed `±5%` UI with computed safe activity radius display
- [X] T051 Remove misleading today-tab placeholder risk values
- [X] T052 Add regression tests for price status and safe activity radius
- [X] T053 Sync `docs/plan.md`, `docs/PRD.md`, `spec/supabase-direct-read.md`, `docs/task.md`, `research.md`, `docs/research.md`

## 메모
- 기존 direct-read 전환 `45/45` 완료 문맥은 유지된다.
- 이번 문서에서는 그 위에 붙은 후속 개선 `27개`까지 합산해 `72/72` 완료로 본다.

## plan 기반 후속 생성 태스크

### 기능명
먹이탐색 안정성 고도화

### 문서 기준
- plan: `C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\plan.md`
- product spec 대체: `C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\PRD.md`
- interface spec: `C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\spec\supabase-direct-read.md`
- research: `C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\research.md`
- quickstart: `C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\quickstart.md`

### Phase 9. Setup
- [X] T054 Create next-iteration task tracking appendix in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\task.md

### Phase 10. Foundational
- [X] T055 Create failing direct-read contract checks for search-result availability metadata in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_public_views_contract.py
- [X] T056 [P] Create failing regression test for representative US fallback ingestion in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_daily_refresh.py
- [X] T057 [P] Create failing search-result badge rendering test in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\tests\us2-search-list.test.ts

### Phase 11. User Story 5 - 검색 전에 가격 준비 상태를 안다
독립 테스트 기준:
- 검색 결과에서 종목을 선택하기 전에도 `live`, `fallback`, `missing` 중 어떤 상태인지 배지로 구분돼야 한다.
- `missing` 상태 종목은 선택 전부터 `가격 준비중` 기대치를 줄 수 있어야 한다.

- [X] T058 [US5] Extend public search contract with price availability fields in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\supabase\migrations\20260322_public_market_views.sql
- [X] T059 [P] [US5] Select search availability fields in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\lib\supabase-queries.js
- [X] T060 [P] [US5] Normalize search availability metadata in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\lib\supabase-adapters.js
- [X] T061 [US5] Render live/fallback/missing search badges in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\lib\direct-read-runtime.js

### Phase 12. User Story 6 - 대표 US 종목 가격 공백을 더 줄인다
독립 테스트 기준:
- `yfinance` 1차 수집이 비더라도 `AAPL`, `TSLA`는 fallback 적재 또는 명확한 상태 하향으로 카드 탐색이 가능해야 한다.
- 이번 배치 실패가 직전 snapshot 가격을 덮어써서 `missing`으로 악화되면 안 된다.

- [X] T062 [US6] Add failing fallback-provider test for representative US symbols in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_market_ingestion_smoke.py
- [X] T063 [US6] Implement Yahoo chart fallback path for representative US snapshots in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\services\us_market_ingestion.py
- [X] T064 [US6] Preserve previous representative prices when current US provider returns partial empty rows in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\scripts\daily_refresh.py
- [X] T065 [US6] Tighten representative-symbol quality gate around `missing` regressions in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_direct_read_quality_gate.py

### Phase 13. User Story 7 - 활동반경 근거를 더 신뢰할 수 있다
독립 테스트 기준:
- 활동반경 문구가 시장 리스크와 종목 변동성 변화에 따라 일관되게 바뀌어야 한다.
- 카드에서 계산 기준이 바뀌어도 범위 `1.5% ~ 6.0%`와 단계가 유지돼야 한다.

- [X] T066 [US7] Create failing label-coverage tests for safe activity radius narratives in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_activity_radius_policy.py
- [X] T067 [US7] Refine safe activity label generation for market-risk and stock-volatility combinations in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\services\activity_radius_policy.py
- [X] T068 [P] [US7] Render stronger activity-level visual distinction in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\index.html
- [X] T069 [US7] Add card-level regression coverage for safe activity badge and caption updates in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\tests\us1-default-cards.test.ts

### Phase 14. Polish & Cross-Cutting
- [X] T070 Update quickstart validation commands for the next iteration in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\quickstart.md
- [X] T071 [P] Sync follow-up scope and remaining risks in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\research.md
- [X] T072 [P] Sync follow-up scope and remaining risks in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\research.md

### 의존성 그래프
- US5 -> US6 -> US7
- 이유:
  - US5가 검색 단계 기대치 문제를 먼저 해결한다.
  - US6이 대표 US 적재 안정성을 보강해 가격 공백 자체를 줄인다.
  - US7이 활동반경 문구와 표현 신뢰도를 다듬는다.

### 병렬 실행 예시
- US5
  - T059와 T060은 병렬 가능
- US6
  - T062와 T065는 병렬 가능
- US7
  - T068와 T069는 병렬 가능
- Polish
  - T071와 T072는 병렬 가능

### 구현 전략
- MVP는 US5만 먼저 완료해 검색 단계 혼란을 줄이는 거다.
- 그다음 US6으로 대표 US 가격 공백을 줄이고,
- 마지막으로 US7에서 활동반경 표현을 고도화한다.
