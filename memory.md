# AntGravity SoYeon Memory

## 작성시각
2026-03-22 21:39:53 KST

## 현재 한 줄 상태
- 현재 주식 모드는 `정적 HTML + Supabase direct-read + tiered batch ingestion` 기준으로 동작한다.
- 브라우저 주 읽기 경로는 `v_home_summary`, `v_stock_search`, `v_stock_detail_latest` direct-read다.
- backend는 `rollback-only` 문맥이지만, 배치 적재 쪽은 `hot/warm/cold`, `fresh/stale/missing`, `exact-worker` 구조까지 구현됐다.

## 현재 브랜치와 기준 커밋
- 현재 브랜치: `codex/ingestion-coverage-v2`
- 기준 커밋: `5ce9326 feat: add tiered ingestion coverage pipeline`
- 직전 주요 커밋:
  - `9176b52 fix: harden direct-read search and fallback coverage`
  - `dfe7625 fix: preserve home summary coverage during refresh`

## 이번 세션에서 실제로 구현된 기준

### 1. 적재 계층 구조
- market별 상위 `200` 종목은 `hot`
- non-hot 중 최근 성공 이력이 `14일` 안이면 `warm`
- 나머지는 `cold`
- `warm`은 `refresh_bucket` `0~11`에 배정돼 `2시간` 순환 적재한다

### 2. 상태/실패/요청 테이블
- 새 테이블:
  - `symbol_ingestion_state`
  - `symbol_ingestion_failure_log`
  - `symbol_refresh_requests`
- `symbol_ingestion_state`는 아래를 저장한다
  - `coverage_tier`
  - `freshness_status`
  - `last_attempted_at`
  - `last_succeeded_at`
  - `last_snapshot_at`
  - `last_price`
  - `last_price_source`
  - `last_error_code`
  - `last_error_message`
  - `consecutive_failures`
- `symbol_ingestion_failure_log`는 phase/provider/error를 append-only로 남긴다
- `symbol_refresh_requests`는 운영/수동 exact 적재 큐다

### 3. 배치 phase dispatcher
- `backend/scripts/daily_refresh.py` phase:
  - `all`
  - `scheduled`
  - `universe-sync`
  - `kr-hot`
  - `us-hot`
  - `warm-rotate`
  - `exact-worker`
  - `summary`
- `scheduled`는 내부 시간 게이트로 필요한 phase만 실행한다
- `summary rebuild`는 각 snapshot batch 성공 직후 자동 실행된다
- `exact-worker`는 `symbol_refresh_requests.status='queued'`만 처리한다

### 4. KR 공급자 구조
- KR 공급자는 코드상 `krx_official -> yfinance_fallback` 구조다
- 현재 `KRX_AUTH_KEY`가 비어 있으면 `resolve_kr_price_provider()`가 `yfinance_fallback`을 선택한다
- 키가 들어오면 코드 수정 없이 `krx_official`로 전환되게 설계됐다
- `PyKRX`는 hot/warm 적재 주 경로가 아니다

### 5. 공개 뷰 확장
- 실제 coverage/freshness 확장은 `supabase/migrations/20260323000100_ingestion_coverage_v2.sql` 기준이다
- `v_stock_search` 추가 컬럼:
  - `coverage_tier`
  - `freshness_status`
  - `last_succeeded_at`
  - `last_snapshot_at`
- `v_stock_detail_latest` 추가 컬럼:
  - `coverage_tier`
  - `freshness_status`
  - `last_succeeded_at`
  - `last_attempted_at`
  - `stale_age_hours`

### 6. 프론트 direct-read 정렬 기준
- 검색 query는 coverage/freshness metadata까지 select한다
- 검색 정렬은 아래 순서다
  1. exact/prefix/contains
  2. `fresh > stale > missing`
  3. `live > fallback > missing`
- 카드 mock/test 타입에도 `coverage_tier`, `freshness_status`, `last_succeeded_at`, `last_attempted_at`, `stale_age_hours`가 반영됐다

### 7. workflow 기준
- `.github/workflows/daily-market-refresh.yml`는 `30분`마다 `scheduled` phase를 호출한다
- workflow_dispatch 기본 phase도 `scheduled`다
- exact worker `3분`은 GitHub Actions가 아니라 외부 워커/크론 전제다

### 8. Supabase migration 상태
- remote/local migration history 기준:
  - `20260321`
  - `20260322`
  - `20260323000100`
- `20260323000100_ingestion_coverage_v2.sql`이 실제 확장 migration이다
- 기존 `20260322`는 baseline public view migration으로 유지된다

## 실제로 확인한 현재 상태

### 검증 결과
- `pnpm lint` 통과
- `pnpm typecheck` 통과
- `pnpm test` 통과
  - 현재 기준 `7 files`, `17 tests`
- `python -m pytest backend/tests` 통과
  - 현재 기준 `47 tests`

### Supabase 상태
- `npx.cmd supabase db push --yes --debug`로 `20260323000100_ingestion_coverage_v2.sql` 원격 반영 완료
- `npx.cmd supabase migration list` 기준 local/remote history는 `20260321 / 20260322 / 20260323000100`로 맞는다

## 현재 구현 기준 구조

### 프론트
- 정적 `index.html` 중심
- 브라우저는 Supabase 공개 뷰만 직접 읽는다
- backend read API는 주 경로가 아니다
- 검색은 freshness/availability metadata를 같이 읽고 정렬한다
- 카드 UI는 단일 카드 1장이다

### 데이터/배치
- Source of Truth
  - `ticker_universe`
  - `market_snapshot_daily`
  - `fundamentals_cache`
  - `market_summary_cache`
- 상태/운영 테이블
  - `symbol_ingestion_state`
  - `symbol_ingestion_failure_log`
  - `symbol_refresh_requests`
- 공개 뷰
  - `v_home_summary`
  - `v_stock_search`
  - `v_stock_detail_latest`

### 운영 cadence
- `universe-sync`: 하루 1회
- `kr-hot`: 한국 장중 30분
- `us-hot`: 미국 정규장 기준 30분
- `warm-rotate`: 2시간
- `exact-worker`: 외부 워커 3분
- `summary`: 각 snapshot batch 직후

## 아직 남은 문제와 주의점

### 1. exact-worker 외부 런타임 미구성
- 코드와 queue 테이블은 들어갔다
- 실제 `3분` 외부 크론/워커 연결은 아직 안 했다

### 2. KR 공식 KRX 실운영 전환 전
- `KRX_AUTH_KEY`가 아직 없어서 현재 KR 운영 경로는 `yfinance_fallback`이다
- KRX key가 들어오면 env만 주입하고 재검증하면 된다

### 3. unrelated 워킹트리 변경 남음
- 아래 항목은 이번 구현 커밋 범위 밖으로 아직 남아 있다
  - `backend/core/supabase_client.py`
  - `backend/services/market_query_service.py`
  - `docs/PRD.md`
  - `docs/plan.md`
  - `docs/quickstart.md`
  - `docs/research.md`
  - `docs/task.md`
  - `docs/운영가이드/github-secrets.md`
  - `research.md`
  - `spec/supabase-direct-read.md`
  - `src/lib/direct-read-runtime.js`
  - `error.png`
  - `docs/working-tree-audit.md`
  - `memory.md`
- 다음 세션에서 커밋/PR 작업 전 반드시 `git status`로 이번 브랜치 커밋 범위와 unrelated 변경을 다시 분리해야 한다

## 새 세션에서 바로 할 것
1. `git status`로 current unstaged 변경 범위부터 확인하기
2. `memory.md` 기준으로 현재 배치 구조가 `hot/warm/cold + fresh/stale/missing`인지 다시 확인하기
3. `symbol_ingestion_state`와 `v_stock_search`를 SQL로 조회해 coverage/freshness 값이 기대대로 채워지는지 확인하기
4. exact-worker 외부 `3분` 런타임을 작업 스케줄러나 외부 크론으로 연결하기
5. `KRX_AUTH_KEY`를 받을 수 있으면 KR provider가 `krx_official`로 전환되는지 실검증하기

## 참고 문서
- `docs/개발일지/2026-03-22-적재범위-개편-v2-구현.md`
- `docs/개발일지/2026-03-22-supabase-migration-push-및-이력-정리.md`
- `docs/prompt/2026-03-22-적재범위-개편-v2-구현.md`
- `docs/prompt/2026-03-22-supabase-migration-push-및-이력-정리.md`

## 추가 업데이트 2026-03-22 22:42:54 KST

### 생존일지 저장/삭제
- 생존일지는 이제 브라우저 `localStorage` 기준으로 실제 저장/삭제가 된다.
- 저장 payload는 `id`, `createdAt`, `moodEmoji`, `moodLabel`, `content`를 가진다.
- 과거의 기록 목록은 더 이상 고정 예시 카드가 아니라 저장된 데이터로 렌더링된다.
- 기록별 `삭제` 버튼으로 즉시 제거할 수 있다.

### 이번 단계에서 확인한 것
- `pnpm lint` 통과
- `pnpm typecheck` 통과
- `pnpm test` 통과
  - 현재 기준 `8 files`, `19 tests`
- 브라우저에서 생존일지 저장은 동작했고, 안 보이는 경우 강한 새로고침이 필요할 수 있다.

### 주의점
- 이 저장은 Supabase 동기화가 아니라 브라우저 로컬 저장이라 기기 간 공유는 안 된다.
- 현재 워킹트리에는 이번 작업과 무관한 다른 변경도 계속 남아 있으니 커밋 범위를 분리해야 한다.
