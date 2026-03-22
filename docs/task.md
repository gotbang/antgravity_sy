# AntGravity Supabase 직결 전환 Tasks

## 작성시각
2026-03-22 11:52:05 KST

## 문서 목적
이 문서는 `.specify`와 `spec.md`가 없는 현재 저장소에서 `docs/plan.md`를 기준으로 user story를 복원해 만든 실행용 task 문서다. 기존 track형 체크리스트를 대체하며, Supabase 직결 전환 구현을 phase와 user story 단위로 바로 수행할 수 있게 적는다.

## 전제 메모
- 기준 문서
  - `docs/plan.md`
  - `docs/research.md`
  - `docs/quickstart.md`
- 기준 가정
  - 대표 KR 품질 게이트 종목: `000660.KS`
  - freshness 기준: `20시간`
  - 전환 방식: `일괄 전환`
  - 폴백 원칙: `배치 품질 우선`
  - 트렌딩은 이번 직결 범위에서 제외하고 보류
- 테스트는 AGENTS 기준 TDD 원칙을 따른다.

## User Story 매핑

### US1 (P1)
오늘 탭과 기본 카드가 Supabase 직결 조회로 동작한다.

독립 테스트 기준:
- 오늘 탭이 `v_home_summary`로 렌더된다.
- 기본 카드 `AAPL`, `TSLA`가 `v_stock_detail_latest`로 렌더된다.
- 브라우저 네트워크에서 `/api/market-summary`, 기본 카드용 `/api/stocks/{symbol}` 호출이 없다.

### US2 (P1)
검색 결과 리스트와 종목 선택이 Supabase 직결 조회로 동작한다.

독립 테스트 기준:
- 검색 결과가 최대 8건 리스트로 노출된다.
- 클릭/Enter/방향키/Escape가 동작한다.
- 선택 후 카드 1이 `v_stock_detail_latest` 결과로 갱신된다.
- 브라우저 네트워크에서 `/api/stocks/search`, 검색용 `/api/stocks/{symbol}` 호출이 없다.

### US3 (P2)
공개 뷰, RLS, 적재 품질 게이트가 직결 구조를 안전하게 지지한다.

독립 테스트 기준:
- `anon`은 뷰 3개만 읽을 수 있다.
- `market_summary_cache.home`가 빈 snapshot 기본값으로 반복 저장되지 않는다.
- `AAPL`, `TSLA`, `000660.KS`가 품질 게이트를 통과한다.
- freshness `20시간` 기준을 만족한다.

### US4 (P3)
컷오버, 레거시 정리, 롤백 가능 상태, 문서/검증 체계가 갖춰진다.

독립 테스트 기준:
- 컷오버 체크리스트를 모두 점검할 수 있다.
- 레거시 FastAPI 읽기 경로가 rollback-only 문맥으로 재분류된다.
- 브라우저 번들에 `SUPABASE_SERVICE_ROLE_KEY`, `DART_API_KEY`가 없다.

## Phase 1. Setup

목표:
- 브라우저 Supabase 읽기 구조와 pnpm 기반 검증 환경의 최소 준비를 끝낸다.

- [X] T001 Create root pnpm workspace manifest in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\package.json
- [X] T002 [P] Create frontend TypeScript config for browser-query tests in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\tsconfig.json
- [X] T003 [P] Create Vitest configuration for direct-read browser tests in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\vitest.config.ts
- [X] T004 [P] Create public runtime config template for `SUPABASE_URL` and `SUPABASE_ANON_KEY` in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\config\public-env.js
- [X] T005 [P] Create browser Supabase client bootstrap module in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\lib\supabase-browser.js

## Phase 2. Foundational

목표:
- 공개 뷰, RLS, adapter, query layer 같은 직결 공통 선행조건을 먼저 완성한다.

- [X] T006 Create failing contract tests for public views and grants in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_public_views_contract.py
- [X] T007 [P] Create failing adapter mapping tests for home/search/detail direct-read payloads in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\tests\supabase-direct-mapping.test.ts
- [X] T008 [P] Create failing direct-read query tests for representative symbols in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\tests\supabase-direct-query.test.ts
- [X] T009 Implement public views, grants, and RLS migration for `v_home_summary`, `v_stock_search`, `v_stock_detail_latest` in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\supabase\migrations\20260322_public_market_views.sql
- [X] T010 [P] Implement browser query helpers for the three public views in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\lib\supabase-queries.js
- [X] T011 [P] Implement snake_case to UI adapter mappings and freshness guards in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\lib\supabase-adapters.js
- [X] T012 [P] Sync frontend runtime and secret prerequisites for direct-read setup in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\quickstart.md

## Phase 3. User Story 1 - 오늘 탭과 기본 카드 직결

Story goal:
- 오늘 탭과 기본 카드 2개를 FastAPI 없이 공개 뷰에서 직접 읽는다.

독립 테스트 기준:
- 오늘 탭이 `v_home_summary`로 렌더된다.
- `AAPL`, `TSLA` 카드가 `v_stock_detail_latest`로 렌더된다.
- `/api/market-summary`와 기본 카드용 `/api/stocks/{symbol}` 호출이 0회다.

- [X] T013 [US1] Create failing today-tab direct-read regression test in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\tests\us1-home-summary.test.ts
- [X] T014 [P] [US1] Create failing default-card direct-read regression test in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\tests\us1-default-cards.test.ts
- [X] T015 [US1] Replace today-tab `/api/market-summary` fetch flow with `v_home_summary` query in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\index.html
- [X] T016 [US1] Replace default-card `/api/stocks/{symbol}` fetch flow with `v_stock_detail_latest` queries in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\index.html
- [X] T017 [US1] Reclassify legacy read helpers for today/default-card usage in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\lib\apiClient.ts

## Phase 4. User Story 2 - 검색 리스트와 종목 선택 직결

Story goal:
- 검색 결과 리스트와 선택 상호작용을 Supabase 직결 구조로 바꾼다.

독립 테스트 기준:
- 검색 결과가 최대 8건 리스트로 노출된다.
- 클릭/Enter/방향키/Escape가 동작한다.
- 선택 후 카드 1이 직결 상세 조회로 갱신된다.
- `/api/stocks/search`와 검색용 `/api/stocks/{symbol}` 호출이 0회다.

- [ ] T018 [US2] Create failing search-result list rendering test in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\tests\us2-search-list.test.ts
- [ ] T019 [P] [US2] Create failing keyboard selection interaction test in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\tests\us2-search-keyboard.test.ts
- [ ] T020 [US2] Replace search source from `/api/stocks/search` to `v_stock_search` in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\index.html
- [ ] T021 [US2] Implement search dropdown, loading, empty, and error states in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\index.html
- [ ] T022 [US2] Implement click, Enter, ArrowUp, ArrowDown, and Escape result selection flow in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\index.html
- [ ] T023 [US2] Replace selected-symbol detail refresh with `v_stock_detail_latest` query in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\index.html

## Phase 5. User Story 3 - 공개 뷰와 적재 품질 게이트 강화

Story goal:
- 공개 뷰/RLS/적재 품질이 직결 구조를 안정적으로 지지하도록 만든다.

독립 테스트 기준:
- `anon`은 공개 뷰만 읽을 수 있다.
- `market_summary_cache.home`가 빈 snapshot 기본값으로 반복 저장되지 않는다.
- `AAPL`, `TSLA`, `000660.KS`가 품질 게이트를 통과한다.
- freshness `20시간` 기준을 만족한다.

- [ ] T024 [US3] Create failing cache freshness gate tests for the `20시간` 기준 in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_cache_freshness_gate.py
- [ ] T025 [P] [US3] Create failing representative-symbol quality gate tests for `AAPL`, `TSLA`, `000660.KS` in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_direct_read_quality_gate.py
- [ ] T026 [P] [US3] Create failing search ranking contract tests for `삼성`, `하이닉스`, `AAPL` in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_search_rank_contract.py
- [ ] T027 [US3] Prevent empty-summary overwrite during batch refresh in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\scripts\daily_refresh.py
- [ ] T028 [US3] Align cache freshness logic with the `20시간` direct-read contract in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\services\supabase_cache_service.py
- [ ] T029 [US3] Improve KR snapshot completeness for representative symbol coverage in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\services\kr_market_ingestion.py
- [ ] T030 [US3] Implement search ordering contract in the public search view migration in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\supabase\migrations\20260322_public_market_views.sql
- [ ] T031 [US3] Sync legacy read-path quality assumptions with direct-read gates in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\services\market_query_service.py

## Phase 6. User Story 4 - 컷오버, 레거시, 롤백 준비

Story goal:
- 컷오버, 레거시 재분류, 롤백 문맥, 운영/보안 검증을 갖춘다.

독립 테스트 기준:
- 컷오버 체크리스트를 모두 실행할 수 있다.
- 레거시 FastAPI 읽기 경로가 rollback-only로 문서화된다.
- 브라우저 번들에 `SUPABASE_SERVICE_ROLE_KEY`, `DART_API_KEY`가 없다.

- [ ] T032 [US4] Create failing browser network regression test for zero legacy read calls in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\tests\us4-cutover-network.test.ts
- [ ] T033 [P] [US4] Create failing rollback-path verification test for legacy read helpers in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_legacy_read_fallback_contract.py
- [ ] T034 [US4] Remove frontend runtime dependence on legacy read helpers in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\src\lib\apiClient.ts
- [ ] T035 [US4] Reclassify FastAPI read routes as rollback-only in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\plan.md
- [ ] T036 [US4] Sync cutover execution steps and rollback runbook in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\quickstart.md
- [ ] T037 [US4] Verify direct-read secret exposure boundaries in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\운영가이드\github-secrets.md

## Phase 7. Polish & Cross-Cutting

목표:
- placeholder 테스트, 문서 부채, 후속 보류 항목을 정리한다.

- [ ] T038 [P] Replace placeholder daily-refresh assertions with real checks in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_daily_refresh.py
- [ ] T039 [P] Replace placeholder ingestion smoke assertions with real checks in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_market_ingestion_smoke.py
- [ ] T040 [P] Replace placeholder sensitive-data guard assertions with real checks in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\backend\tests\test_sensitive_data_guard.py
- [ ] T041 Update `docs/task.md` execution notes and story summary after implementation lands in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\task.md
- [ ] T042 Sync freshness references from `25시간` to `20시간` in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\plan.md
- [ ] T043 Create canonical product requirements placeholder aligned to the direct-read plan in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\PRD.md
- [ ] T044 Create implementation spec placeholder for the direct-read contract in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\spec\supabase-direct-read.md
- [ ] T045 Sync implementation outcomes and deferred scope notes in C:\Users\khc\Desktop\fastcampus\ant_gravity_soyeon\docs\research.md

## Dependencies

### Phase dependencies
- Phase 1 완료 후 Phase 2 진행
- Phase 2 완료 후 US1, US2, US3 진행 가능
- US4는 US1, US2, US3 완료 후 진행
- Phase 7은 US4 완료 후 진행

### User story completion order
1. `US1`
2. `US2`
3. `US3`
4. `US4`

### Story dependency notes
- `US1`은 MVP의 첫 완료 단위다.
- `US2`는 `US1`의 query/adapter 기반을 재사용하지만, 사용자 가치 기준으로 별도 검증 가능하다.
- `US3`는 기능 추가보다 직결 구조의 품질/권한/적재 안정화를 담당한다.
- `US4`는 컷오버와 레거시/롤백 문맥을 정리하는 마감 단계다.

## Parallel execution examples

### Setup
- `T002`, `T003`, `T004`, `T005`는 `T001` 이후 병렬 가능

### Foundational
- `T007`, `T008`은 `T006` 이후 병렬 가능
- `T010`, `T011`, `T012`는 `T009`와 충돌 없는 범위에서 병렬 가능

### US1
- `T014`는 `T013`과 별개 파일이라 병렬 가능

### US2
- `T019`와 `T020`은 테스트 작성 후 같은 `index.html`을 만지므로 순차 진행 권장

### US3
- `T025`, `T026`은 `T024` 이후 병렬 가능
- `T028`, `T029`, `T030`은 서로 다른 파일이라 병렬 가능

### US4
- `T033`은 `T032` 이후 병렬 가능
- `T035`, `T036`, `T037`은 서로 다른 문서라 병렬 가능

### Polish
- `T038`, `T039`, `T040`은 병렬 가능
- `T043`, `T044`, `T045`는 병렬 가능

## Implementation strategy

### MVP 우선 전략
- MVP 범위는 Phase 1, Phase 2, `US1`까지다.
- 이 시점에서 오늘 탭과 기본 카드 2개가 Supabase 직결로 동작해야 한다.

### Incremental delivery
1. Setup + Foundational로 공개 뷰와 브라우저 읽기 기반을 만든다.
2. `US1`로 오늘 탭과 기본 카드를 먼저 전환한다.
3. `US2`로 검색 리스트와 선택 UX를 전환한다.
4. `US3`로 권한, 적재, 품질 게이트를 강화한다.
5. `US4`로 컷오버와 레거시/롤백 문맥을 정리한다.
6. Final Phase에서 placeholder 테스트와 문서 부채를 정리한다.

### 완료 기준
- 모든 태스크가 checklist 형식을 따른다.
- 모든 user story phase에 독립 테스트 기준이 있다.
- 공개 뷰, RLS, 직결 조회, 품질 게이트, 컷오버, 롤백이 문서에 모두 연결돼 있다.
