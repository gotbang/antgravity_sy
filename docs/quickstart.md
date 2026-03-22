# Quickstart

## 작성시각
2026-03-22 15:42:41 KST

## 문서 목적
이 문서는 현재 저장소 기준 실제 실행 경로와 검증 경로를 정리한다. 지금 주식 모드의 기준 구조는 direct-read 기준이다.

## 1. 현재 실행법

### 백엔드 의존성 설치
- `python -m pip install -r backend/requirements.txt`

### 프론트 의존성 설치
- `pnpm install`

### 공개 env 동기화
- `pnpm run sync:public-env`

### 로컬 실행 권장 경로
- `pnpm run dev`
- 이 명령은 루트 `.env`의 `SUPABASE_URL`, `SUPABASE_ANON_KEY`를 `src/config/public-env.generated.js`로 반영한 뒤 정적 서버를 띄운다.

### 대체 실행 경로
- `python -m http.server 8080`
- 이 경우에도 먼저 `pnpm run sync:public-env`를 실행해 공개 env 파일을 갱신해야 한다.

### 배치 스크립트 실행
- `cmd`
  - `set PYTHONPATH=backend`
  - `python backend/scripts/daily_refresh.py --phase all`
- `PowerShell`
  - `$env:PYTHONPATH='backend'`
  - `python backend/scripts/daily_refresh.py --phase all`

## 2. 현재 필요한 환경값

### 브라우저 direct-read
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

### 백엔드/배치
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DART_API_KEY`
- `ALLOWED_ORIGINS`

## 3. 현재 검증 명령

### 프론트
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`

### 백엔드
- `python -m pytest backend/tests/test_public_views_contract.py backend/tests/test_cache_freshness_gate.py backend/tests/test_direct_read_quality_gate.py backend/tests/test_search_rank_contract.py backend/tests/test_legacy_read_fallback_contract.py backend/tests/test_daily_refresh.py backend/tests/test_market_ingestion_smoke.py backend/tests/test_sensitive_data_guard.py backend/tests/test_activity_radius_policy.py`

## 4. 현재 실제 동작 메모
- 오늘 탭은 `v_home_summary` direct-read 기준으로 동작한다.
- 먹이 탐색 탭은 단일 종목 카드만 보인다.
- 기본 카드는 `AAPL`로 시작한다.
- 검색 결과 리스트는 direct-read 기반으로 동작한다.
- `하이닉스` 검색 후 `SK하이닉스 / 000660.KS / KR` 선택 시 카드 1 가격 `₩1,007,000`을 확인했다.
- 검색 결과에는 `실시간`, `캐시`, `가격 준비중` 상태 배지가 함께 표시된다.
- 대표 US 종목 `AAPL`, `TSLA`는 `yfinance` 실패 시 Yahoo chart fallback 경로로 재시도한다.

## 5. 배치/자동화 메모
- GitHub Actions workflow 파일은 `.github/workflows/daily-market-refresh.yml`에 있다.
- 현재 workflow는 `actions/checkout@v5`, `actions/setup-python@v6`를 사용한다.
- workflow는 실행 전에 아래 시크릿을 먼저 검증한다.
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DART_API_KEY`
- 자동 스케줄은 `0 22 * * 0-4`다.
  - GitHub UTC 기준
  - 한국 기준 월~금 오전 7시
- 수동 실행은 GitHub Actions `Daily Market Refresh`에서 `phase=all`로 돌리면 된다.

## 6. rollback-only 메모
- `/api/market-summary`
- `/api/stocks/search`
- `/api/stocks/{symbol}`

위 세 경로는 현재 신규 주 경로가 아니라 rollback-only 경로다.
