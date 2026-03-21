# AntGravity 실데이터 연동 Tasks

## 작성시각
2026-03-21 19:50:52 KST

## 구현 전략 요약
- 기준 문서: `docs/plan.md`의 `7. 실데이터 연동 계획`
- 최신 우선 원칙으로 `실데이터 연동`만 task 범위로 잡고, 기존 리디자인 계획은 참고 전제로만 본다.
- 핵심 전제:
  - `시장 데이터만 실데이터`
  - `Supabase 원본`
  - `파일 캐시 비추적 산출물`
  - `미국장 마감 후 하루 1회`
  - `생존 일지 = localStorage 유지`
  - `개미 광장 실데이터 제외`

## MVP 권장 범위
- MVP는 `US1`만 먼저 완료하는 방식으로 간다.
- 이유: KR/US 데이터 적재, Supabase 원본, 배치/캐시 정책이 먼저 안정돼야 이후 API/프론트 연결이 흔들리지 않는다.

## 의존성 순서
- `US1 -> US2 -> US3`

## 독립 테스트 기준
- `US1`: KR/US 샘플 종목이 수집되어 Supabase에 upsert되고 배치가 재실행 가능해야 한다.
- `US2`: 4개 API가 Supabase 원본과 부분 폴백 규칙대로 응답해야 한다.
- `US3`: 현재 화면 구조를 바꾸지 않고 시장 데이터 카드만 실데이터 응답에 연결되어야 한다.

---

## Phase 1: Setup

- [X] T001 Python 기반 데이터 파이프라인 구조를 위한 `backend/`, `backend/services/`, `backend/routers/`, `backend/scripts/`, `backend/tests/`, `supabase/migrations/` 디렉터리 생성 계획을 `docs/plan.md`와 맞춰 확정
- [X] T002 `backend/requirements.txt`에 `dartlab[all]`, `pykrx`, `yfinance`, `supabase`, `python-dotenv`, `fastapi`, `uvicorn`, `httpx`, `pytest` 의존성 추가
- [X] T003 `.env.example`에 `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DART_API_KEY`를 추가하고 `미국장 마감 후 하루 1회` 배치 전제를 주석으로 명시
- [X] T004 `docs/운영가이드/github-secrets.md`를 생성해 GitHub Actions 시크릿과 파일 캐시 비추적 산출물 원칙을 기록

## Phase 2: Foundational

- [X] T005 Supabase 원본 구조를 위해 `supabase/migrations/20260321_market_data_foundation.sql`에 `ticker_universe`, `market_snapshot_daily`, `fundamentals_cache`, `market_summary_cache` 테이블과 인덱스 설계 추가
- [X] T006 `backend/services/supabase_cache_service.py`에 Supabase read/write 공통 계층 설계 및 `in-memory -> Supabase -> 부분 폴백` 우선순위 헬퍼 구현
- [X] T007 [P] `backend/services/cache_policy.py`에 가격 온디맨드 보충 허용, 재무/공시/AI 집계 batch-only 규칙을 상수와 정책 함수로 정의
- [X] T008 [P] `backend/tests/test_cache_policy.py`에 부분 폴백 정책과 batch-only 정책을 검증하는 단위 테스트 추가

---

## Phase 3: User Story 1 - KR/US 실데이터 수집, 적재, 캐시 기반 마련

**목표**: KR/US 전체 시장 데이터를 수집해 Supabase에 적재하고, 배치와 캐시 원칙이 안정적으로 동작하게 만든다.

**독립 테스트 기준**: KR/US 샘플 종목 적재 성공, Supabase upsert 성공, 배치 재실행 가능

- [X] T009 [US1] `backend/tests/test_market_ingestion_smoke.py`에 KR/US 샘플 데이터 적재 smoke 테스트 추가
- [X] T010 [P] [US1] `backend/services/kr_market_ingestion.py`에 `PyKRX` 기반 KR 전체 종목 유니버스/가격/거래대금/시총 수집 로직 구현
- [X] T011 [P] [US1] `backend/services/kr_fundamentals_ingestion.py`에 `Dartlab/OpenDART` 기반 KR 공시/재무 수집 로직 구현
- [X] T012 [P] [US1] `backend/services/us_market_ingestion.py`에 `SEC EDGAR` 기반 미국 전체 종목 유니버스 수집과 `yfinance` 가격/기초지표 수집 로직 구현
- [X] T013 [US1] `backend/services/market_summary_builder.py`에 시장 심리, 감정 지표, AI 분석 카드용 집계 데이터 생성 로직 구현
- [X] T014 [US1] `backend/scripts/daily_refresh.py`에 KR/US 수집 -> Supabase upsert -> market summary 갱신 순서의 일배치 스크립트 구현
- [X] T015 [US1] `.github/workflows/daily-market-refresh.yml`에 `미국장 마감 후 하루 1회` cron과 `workflow_dispatch` 수동 실행 추가
- [X] T016 [US1] `.gitignore`에 런타임 보조 파일 캐시 경로를 추가해 파일 캐시를 비추적 산출물로 고정
- [X] T017 [US1] `backend/tests/test_daily_refresh.py`에 배치 재실행과 Supabase upsert 재시도 가능 여부를 검증하는 테스트 추가

---

## Phase 4: User Story 2 - Supabase 원본 기반 API 서빙

**목표**: Supabase 원본과 부분 폴백 규칙을 따르는 API를 제공해 프론트가 실데이터를 소비할 수 있게 만든다.

**독립 테스트 기준**: 4개 API가 Supabase 원본과 부분 폴백 규칙대로 응답

- [X] T018 [US2] `backend/tests/test_market_summary_api.py`에 `GET /api/market-summary` 응답 테스트 추가
- [X] T019 [P] [US2] `backend/tests/test_trending_api.py`에 `GET /api/market/trending` 응답 테스트 추가
- [X] T020 [P] [US2] `backend/tests/test_stock_search_api.py`에 `GET /api/stocks/search` 응답 테스트 추가
- [X] T021 [P] [US2] `backend/tests/test_stock_detail_api.py`에 `GET /api/stocks/:symbol` 응답 테스트 추가
- [X] T022 [US2] `backend/services/market_query_service.py`에 market summary, trending, search, stock detail 조회 로직 구현
- [X] T023 [US2] `backend/routers/market.py`에 `GET /api/market-summary`, `GET /api/market/trending` 엔드포인트 구현
- [X] T024 [US2] `backend/routers/stocks.py`에 `GET /api/stocks/search`, `GET /api/stocks/:symbol` 엔드포인트 구현
- [X] T025 [US2] `backend/main.py`에 market/stocks 라우터 등록과 캐시 정책 초기화 추가
- [X] T026 [US2] `backend/tests/test_partial_fallback.py`에 가격 데이터만 온디맨드 보충되고 재무/공시/AI 집계는 batch-only인 규칙 검증 추가

---

## Phase 5: User Story 3 - 현재 화면 구조 유지 상태에서 시장 데이터 카드만 프론트 연결

**목표**: 현재 UI 구조를 유지한 채 시장 심리, 트렌딩 종목, 검색/상세, 감정 지표, AI 분석 카드만 실데이터에 연결한다.

**독립 테스트 기준**: 현재 화면 구조 유지 상태에서 시장 데이터 카드만 실데이터 반영

- [X] T027 [US3] `src/tests/live-market-binding.test.ts`에 화면 구조를 바꾸지 않고 시장 데이터 카드만 바인딩되는지 검증하는 테스트 추가
- [X] T028 [P] [US3] `src/lib/apiClient.ts`에 `fetchMarketSummary`, `fetchTrending`, `fetchStockSearch`, `fetchStockDetail` API 클라이언트 추가
- [X] T029 [P] [US3] `src/lib/live-data.ts`에 Supabase 원본 API 응답을 기존 화면 데이터 shape로 매핑하는 어댑터 추가
- [X] T030 [US3] `index.html`에서 시장 심리, 트렌딩 종목, AI 분석 카드 렌더링에 필요한 데이터 바인딩 지점만 실데이터로 연결
- [X] T031 [US3] `design/index.html`에서 검색/상세/감정 지표 카드의 데이터 주입 포인트만 실데이터로 연결
- [X] T032 [US3] `src/styles/tokens.css` 또는 현재 프론트 스타일 진입점에서 구조 변경 없이 로딩/빈 상태 표시 클래스만 최소 추가
- [X] T033 [US3] `research.md`에 실데이터 연결 범위와 `개미 광장 제외`, `생존 일지 localStorage 유지`를 구현 결과 기준으로 동기화

---

## Final Phase: Polish & Cross-Cutting Concerns

- [X] T034 `backend/tests/test_sensitive_data_guard.py`에 GPS 및 민감정보 비저장 규칙 테스트 추가
- [X] T035 [P] `docs/plan.md`와 `docs/task.md`에 실제 구현 결과 기준 용어 불일치가 없는지 검토 및 동기화
- [X] T036 [P] `docs/research.md`와 `research.md`에 데이터 소스, 캐시 우선순위, 배치 시점 운영 메모 반영
- [X] T037 `docs/운영가이드/github-secrets.md`와 `.github/workflows/daily-market-refresh.yml`의 시크릿/스케줄 설명 일치 여부 점검
- [X] T038 `pnpm lint`, `pnpm typecheck`, `pnpm test`와 Python 테스트 실행 절차를 `docs/quickstart.md`에 정리

---

## Dependencies

- Setup 완료 후 Foundational 진행
- Foundational 완료 후 `US1` 진행
- `US1` 완료 후 `US2` 진행
- `US2` 완료 후 `US3` 진행
- 모든 스토리 완료 후 Polish 진행

## Parallel Execution Examples

### US1
- T010, T011, T012는 서로 다른 수집 모듈이라 병렬 진행 가능
- T015, T016은 배치와 캐시 산출물 관리라 병렬 진행 가능

### US2
- T018, T019, T020, T021 테스트 작성은 병렬 진행 가능
- T023, T024는 market/stocks 라우터가 분리되면 병렬 진행 가능

### US3
- T028, T029는 API 클라이언트와 매핑 계층이 분리되면 병렬 진행 가능

## Implementation Strategy

### MVP First
1. `US1`만 먼저 완료해서 KR/US 적재와 Supabase 원본을 안정화한다.
2. 그다음 `US2`로 읽기 API를 연다.
3. 마지막에 `US3`로 현재 화면 구조를 유지한 상태에서 시장 데이터 카드만 연결한다.

### Incremental Delivery
1. KR 데이터부터 먼저 수집/적재 성공
2. US 유니버스와 가격 레이어 추가
3. 시장 요약/트렌딩 API 제공
4. 검색/상세 API 제공
5. 현재 화면 구조에 실데이터 바인딩

## Format Validation
- 모든 태스크는 `- [ ] T### ...` 형식을 따른다.
- 사용자 스토리 Phase 태스크는 모두 `[US1]`, `[US2]`, `[US3]` 라벨을 가진다.
- 병렬 가능한 태스크만 `[P]`를 붙였다.
- 모든 태스크에 명확한 파일 경로를 포함했다.
