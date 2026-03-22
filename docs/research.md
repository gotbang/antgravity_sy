# AntGravity 구현 기준 리서치

## 작성시각
2026-03-22 11:21:58 KST

## 문서 목적
이 문서는 `memory.md`, 현재 소스코드, 기존 문서들을 함께 읽고 정리한 구현 기준 리서치다. 현재 저장소에 실제로 구현된 것과 다음 구현 예정으로 남겨둘 것을 분리해서 기록한다.

## 1. 현재 구현 구조

### 프론트
- 메인 엔트리는 정적 `index.html`이다.
- 브라우저는 Supabase를 직접 조회하지 않고 FastAPI `/api/...` 경로를 호출한다.
- 주요 진입 함수는 `refreshMarketSummary()`, `refreshStockCard()`, `performSearch()`, `bindSearch()`다.
- 디자인 참조용 파일로 `design/index.html`, `design/tokens.css`가 있다.

### 백엔드
- FastAPI 엔트리는 `backend/main.py`다.
- 공개 엔드포인트는 아래 5개다.
  - `GET /api/health`
  - `GET /api/market-summary`
  - `GET /api/market/trending`
  - `GET /api/stocks/search`
  - `GET /api/stocks/{symbol}`
- 현재 프론트가 기대하는 실데이터는 모두 이 경로를 통해 들어온다.

### 데이터 저장소와 적재
- Supabase 테이블은 `ticker_universe`, `market_snapshot_daily`, `fundamentals_cache`, `market_summary_cache`를 쓴다.
- `backend/scripts/daily_refresh.py`가 유니버스 수집, snapshot 적재, detail cache 갱신, summary cache 갱신을 수행한다.
- `--phase` 인자는 받지만 실제 분기 로직은 없다.

## 2. 현재 화면과 데이터 바인딩 범위

### 로비 화면
- 부동산 카드: 공사중 토스트
- 주식 카드: 실제 앱 진입
- 코인 카드: 겨울잠 토스트

### 오늘 탭
- `/api/market-summary` 응답을 받아 시장 기분, 공포탐욕 점수, 상승/하락 비율, AI 요약을 갱신한다.
- summary 조회 실패 시 콘솔 에러만 남기고 화면 기본값은 유지한다.

### 먹이 탐색 탭
- 로드시 `AAPL`, `TSLA`를 각각 카드 1, 카드 2에 넣는다.
- 검색은 Enter와 버튼 클릭 둘 다 지원한다.
- 검색 결과 리스트는 아직 없고, 첫 결과만 카드 1에 반영한다.
- 가격 포맷은 `market === 'KR'`일 때 `KRW`, 아니면 `USD` 기준이다.

### 생존 일지 탭
- 감정 선택 UI와 텍스트 입력 UI만 있다.
- 저장 버튼은 아직 저장소와 연결되지 않았다.
- 과거 기록 목록은 정적 예시 마크업이다.

## 3. 현재 구현상 확인된 사실

### 검색 UX
- 문서상 미래 계획으로 적혀 있던 드롭다운 검색은 아직 구현되지 않았다.
- 현재 구현은 “입력 -> API 호출 -> 첫 결과 즉시 카드 1 교체”다.
- `삼성` 검색 시 어떤 종목이 첫 결과로 오느냐에 따라 카드 1 결과가 달라진다.

### 트렌딩
- 백엔드에 `/api/market/trending` 경로는 있다.
- 현재 `index.html`에는 트렌딩 결과를 렌더링하는 UI가 없다.

### 캐시/폴백
- `market_summary`는 캐시가 없으면 503이 가능하다.
- `trending`은 캐시가 없을 때 빈 리스트를 반환할 수 있다.
- `stock detail`은 snapshot이 없을 때 KR 종목에 한해 Yahoo chart API 가격 폴백을 시도한다.
- summary/fundamentals는 라이브 폴백을 허용하지 않는다.

### 보안/민감정보
- 현재 브라우저는 Supabase 키를 직접 쓰지 않는다.
- `SUPABASE_SERVICE_ROLE_KEY`와 `DART_API_KEY`는 서버/배치 문맥이다.
- GPS 저장, 사용자 계정 저장, 생존 일지 저장은 현재 구현에 없다.

## 4. 현재 품질 이슈와 제약

### summary 품질
- `build_market_summary([])`가 빈 입력에서도 기본값을 만들기 때문에, 상위 데이터가 비면 오늘 탭 품질이 낮아질 수 있다.
- `yfinance` 실패로 US snapshot이 비는 경우가 실제 원인 후보다.

### KR 데이터 안정성
- KR snapshot 적재가 항상 안정적인 상태는 아니다.
- 그래서 KR 상세 응답이 snapshot보다 Yahoo chart 가격 폴백에 기대는 경우가 있다.

### 테스트 범위
- 엔드포인트 존재 여부 테스트는 있으나 시나리오 테스트는 얕다.
- placeholder 테스트 3개가 남아 있다.
- 프론트 테스트는 요약 데이터 매핑 1건만 검증한다.

### 프로젝트 구조 제약
- 루트에 `package.json`이 없어 `pnpm lint`, `pnpm typecheck`를 바로 실행할 수 없다.
- `docs/PRD.md`, `spec/`처럼 AGENTS가 기준으로 적은 문서 위치가 아직 실제 저장소에는 없다.

## 5. 다음 구현 예정 사항

### 유지해야 할 후속 기능 계획
- 검색 결과 리스트 드롭다운
- 클릭/Enter/방향키 기반 선택 UX
- 오늘 탭 summary 품질 안정화
- KR snapshot 적재 안정화
- 트렌딩 UI 도입 여부 검토

### 유지해야 할 후속 아키텍처 계획
- `정적 프론트 + Supabase 직결`은 현재 사실이 아니라 후속 검토 안건이다.
- 후속 검토안에서 유지할 읽기 전용 뷰 이름은 아래 3개다.
  - `v_home_summary`
  - `v_stock_search`
  - `v_stock_detail_latest`
- FastAPI 제거는 현재 상태가 아니라, 후속 아키텍처 전환이 승인될 때 검토할 항목이다.

## 6. 이번 리서치 결론
- 현재 저장소의 기준 구조는 `정적 HTML + FastAPI + Supabase`다.
- 문서가 이 사실을 기준으로 먼저 맞춰져야 한다.
- 그렇다고 다음 구현 예정이었던 `검색 리스트`, `Supabase 직결`, `FastAPI 제거 검토`를 지우면 안 되므로, 별도 후속 계획으로 남겨두는 방식이 가장 안전하다.

## 7. 현재 구현 진척 메모
- Setup, Foundational, `US1`, `US2`는 실제 구현이 진행됐다.
- direct-read helper, 공개 뷰 migration, 오늘 탭/기본 카드/검색 리스트 직결 흐름이 들어갔다.
- `US3`, `US4`도 freshness `20시간`, 품질 게이트, rollback-only 문맥까지 코드와 문서에 반영됐다.
- 현재 남은 건 placeholder 테스트 정리와 문서 부채 마무리 위주다.
