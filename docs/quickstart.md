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
- 현재는 별도 Supabase 키가 필요 없다.
- 브라우저는 정적 파일만 띄우고 데이터는 FastAPI가 대신 읽는다.
- 직결 전환 준비용 공개 env 템플릿은 `src/config/public-env.js`에 있다.

## 4. 다음 구현 예정 메모

- 검색 결과 리스트 UX는 아직 구현 전이다.
- `정적 프론트 + Supabase 직결`은 후속 검토 안건으로 남아 있다.
- 만약 그 구조가 승인되면 아래 값이 프론트 런타임 후보가 된다.
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
- 브라우저 Supabase 클라이언트 초기화 모듈은 `src/lib/supabase-browser.js`에 둘 준비가 되어 있다.
- 현재 이 문단은 계획 보존용이고, 실제 실행 기준은 아니다.
