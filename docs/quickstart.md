# Quickstart

## 작성시각
2026-03-22 11:21:58 KST

## 문서 목적
이 문서는 현재 저장소에서 실제로 실행되는 경로를 먼저 적고, 다음 구현 예정인 실행 구조는 별도 메모로 남긴다.

## 1. 현재 실행법

### 백엔드 의존성 설치
- `python -m pip install -r backend/requirements.txt`

### 프론트 검증 의존성 설치
- `pnpm install`

### 브라우저 직결용 공개 env 동기화
- `pnpm run sync:public-env`

### 프론트 검증 명령
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`

### 백엔드 실행
- `python -m uvicorn backend.main:app --reload`

### 배치 스크립트 실행
- `cmd`
  - `set PYTHONPATH=backend`
  - `python backend/scripts/daily_refresh.py --phase all`
- `PowerShell`
  - `$env:PYTHONPATH='backend'`
  - `python backend/scripts/daily_refresh.py --phase all`

### 정적 프론트 실행
- `python -m http.server 8080`
- 또는 `5500` 계열 정적 서버를 써도 된다.
- 현재 CORS 허용값에는 `5173`, `8080`, `5500` localhost 주소가 포함돼 있다.

### 로컬 직결 실행 권장 경로
- `pnpm run dev`
- 이 명령은 루트 `.env`에서 `SUPABASE_URL`, `SUPABASE_ANON_KEY`를 읽어 `src/config/public-env.generated.js`를 갱신한 뒤 정적 서버를 띄운다.

### 확인 경로
- 프론트
  - `/index.html`
  - `/design/index.html`
- 백엔드
  - `/api/health`
  - `/api/market-summary`
  - `/api/market/trending`

## 2. 현재 실행 구조 메모

- 현재 프론트는 FastAPI `/api/...`를 호출한다.
- 현재 브라우저는 Supabase를 직접 읽지 않는다.
- `--phase` 인자는 현재 받고만 있고 실제 분기 동작은 없다.
- 루트에 `package.json`이 없어 지금 상태 그대로는 `pnpm run dev`, `pnpm lint`, `pnpm typecheck`를 실행할 수 없다.

## 3. 현재 필요한 환경값

### 백엔드/배치
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DART_API_KEY`
- `ALLOWED_ORIGINS`

### 브라우저
- direct-read 기준으로는 `SUPABASE_URL`, `SUPABASE_ANON_KEY`가 필요하다.
- 루트 `.env`의 값은 `pnpm run sync:public-env` 또는 `pnpm run dev`로 브라우저용 `src/config/public-env.generated.js`에 반영한다.
- 공개 env 로더는 `src/config/public-env.js`에 있다.

## 4. 다음 구현 예정 메모

- 검색 결과 리스트 UX는 아직 구현 전이다.
- `정적 프론트 + Supabase 직결`은 후속 검토 안건으로 남아 있다.
- 만약 그 구조가 승인되면 아래 값이 프론트 런타임 후보가 된다.
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
- 브라우저 Supabase 클라이언트 초기화 모듈은 `src/lib/supabase-browser.js`에 둘 준비가 되어 있다.
- 현재는 direct-read가 실제 구현됐으므로 로컬 브라우저 실행 시 공개 env 동기화가 필요하다.

## 5. 컷오버/롤백 실행 메모

### 컷오버 확인
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `python -m pytest backend/tests/test_public_views_contract.py backend/tests/test_cache_freshness_gate.py backend/tests/test_direct_read_quality_gate.py backend/tests/test_search_rank_contract.py backend/tests/test_legacy_read_fallback_contract.py`

### rollback-only 경로
- direct-read 전환 이후 `/api/market-summary`, `/api/stocks/search`, `/api/stocks/{symbol}`는 rollback-only 경로로 간주한다.
- 기본 사용자 흐름은 공개 뷰 direct-read가 우선이다.

### 롤백 메모
- direct-read 품질 게이트가 깨지면 프론트 조회 helper를 legacy `/api/...` 경로로 되돌린다.
- 롤백 후에도 공개 뷰와 배치 적재는 유지한다.
