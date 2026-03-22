# AntGravity Supabase direct-read 운영 plan

## 작성시각
2026-03-22 16:20:06 KST

## 문서 목적
이 문서는 현재 주식 모드의 운영 기준을 direct-read 기준으로 고정한다. 이번 갱신에서는 먹이 탐색 가격 공백을 빈칸이 아닌 상태로 처리하고, `안전 활동반경`을 실제 적재 데이터 기반으로 계산해 노출하는 정책까지 포함한다.

## 1. 현재 기준 요약

### 현재 구조
- 프론트 엔트리는 정적 `index.html`이다.
- 브라우저는 `v_home_summary`, `v_stock_search`, `v_stock_detail_latest`를 direct-read 한다.
- 로컬 공개 env는 루트 `.env`에서 `src/config/public-env.generated.js`로 동기화한다.
- 배치 적재는 `backend/scripts/daily_refresh.py`가 맡는다.
- FastAPI 읽기 경로는 rollback-only 레거시 문맥이다.

### 현재 사용자 경험
- 로비에는 부동산, 주식, 코인 3개 모드 카드가 있다.
- 주식 모드에는 `여왕의 지시`, `먹이 탐색`, `생존 일지` 3탭이 있다.
- 오늘 탭은 `v_home_summary` 결과를 바인딩한다.
- 먹이 탐색 탭은 단일 종목 카드 1장만 사용하고 기본 심볼은 `AAPL`이다.
- 검색 결과를 고르면 같은 카드 1장이 선택 종목으로 교체된다.
- 카드 가격은 `price_status`에 따라 `최신 적재 가격`, `캐시 보강 가격`, `가격 준비중`으로 표시된다.
- `안전 활동반경`은 더 이상 고정 `±5%`가 아니라 서버 데이터 계약에서 계산된 값으로 표시된다.
- 생존 일지는 감정 선택과 텍스트 입력 UI만 있고 저장 기능은 아직 없다.

### 현재 검증 상태
- direct-read 공개 뷰 3개 운영 중
- 가격 상태 필드와 활동반경 필드가 `v_stock_detail_latest` 계약에 포함됨
- 배치 적재가 fallback price/status/activity payload를 함께 생성함
- 오늘 탭 placeholder 숫자 제거 완료
- 대표 검증은 프론트 테스트와 배치/계약 테스트 기준으로 유지함

## 2. 범위와 비범위

### 현재 운영 범위
- 오늘 탭 요약 조회
- 종목 검색 결과 리스트 조회
- 선택 종목 상세 카드 조회
- 가격 상태 명시
- 활동반경 실데이터 계산/표시
- direct-read 공개 뷰 3개 운영
- 배치 적재와 품질 게이트 운영
- rollback-only FastAPI 읽기 경로 유지

### 현재 비범위
- 검색 결과 단계 실시간 가격 조회
- 브라우저 단계 라이브 폴백
- 트렌딩 UI 복구
- 생존 일지 저장/복원
- 로그인/계정
- 실시간 시세 스트리밍

## 3. 데이터와 화면 기준

### Source of Truth
- 종목 마스터: `ticker_universe`
- 시세 원본: `market_snapshot_daily`
- 종목 상세 캐시: `fundamentals_cache`
- 홈 요약 캐시: `market_summary_cache`

### 공개 읽기 surface
- `v_home_summary`
- `v_stock_search`
- `v_stock_detail_latest`

### 현재 화면 바인딩
- 오늘 탭
  - `v_home_summary`
  - 시장 기분, 공포탐욕 점수, 상승/하락 비중, AI 요약 표시
  - 로드 실패 시 가짜 숫자를 남기지 않고 로딩/미적재 문구를 유지
- 먹이 탐색
  - 초기 단일 카드: `AAPL`
  - 검색 결과: `v_stock_search`
  - 선택 후 카드 갱신: `v_stock_detail_latest`
  - 가격 포맷: KR=`KRW`, US=`USD`
  - 가격 상태: `live | fallback | missing`
  - 활동반경 필드: `safe_activity_radius_pct`, `safe_activity_level`, `safe_activity_label`
- 생존 일지
  - 입력 UI만 존재
  - 저장 기능은 범위 밖

### 가격 정책
- 우선순위는 `latest snapshot.close -> cache fallback price -> null`
- 끝까지 가격이 없으면 UI는 빈칸 대신 `가격 준비중`을 보여준다.
- 검색 결과 자체는 숨기지 않고 카드 상태 명시를 우선한다.

### 활동반경 정책
- 계산 책임은 프론트가 아니라 서버 데이터 계약에 있다.
- 시작값은 `5.0%`
- 시장 리스크
  - `fearGreedIndex <= 30` 또는 `>= 70`이면 강한 축소
  - `<= 40` 또는 `>= 60`이면 약한 축소
- 종목 리스크
  - `abs(change_pct)`가 클수록 축소
- 유동성 리스크
  - `volume`이 매우 낮으면 추가 축소
  - 값이 없으면 중립
- 최종 범위는 `1.5% ~ 6.0%`
- 단계
  - `>= 4.5%`면 `safe`
  - `>= 3.0%`면 `caution`
  - 그 아래는 `danger`

### 배치 적재 순서
1. KR/US 유니버스를 수집해 `ticker_universe`에 upsert
2. KR/US snapshot을 수집해 `market_snapshot_daily`에 upsert
3. 기존 snapshot과 이번 snapshot을 병합해 가격 누락을 줄인다
4. 홈 요약을 먼저 계산한다
5. 상세 캐시에 가격, 상태, 활동반경, summary를 함께 적재한다
6. 일부 KR 종목 재무/요약 보강 payload를 기존 상세 payload와 merge한다
7. 홈 요약을 `market_summary_cache.home`에 저장한다
8. 일부 snapshot 기반 데이터를 `market_summary_cache.trending`에 저장한다

## 4. 운영 및 보안 기준

### 브라우저 문맥
- 사용 가능 값
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
- 브라우저는 generated env 파일만 읽는다.
- 브라우저는 원본 테이블을 직접 조회하지 않는다.
- 브라우저는 공개 뷰 3개 외 relation을 알 필요가 없게 유지한다.

### 배치/관리 문맥
- 사용 가능 값
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DART_API_KEY`
- 적재, 공개 뷰 생성/관리, 운영 점검은 배치/관리 문맥에서만 수행한다.

### RLS/권한 기준
- 원본 테이블은 `anon`, `authenticated` 직접 조회 금지
- 공개 뷰 3개에만 `anon`, `authenticated` select 허용
- 브라우저 번들에는 `SUPABASE_SERVICE_ROLE_KEY`, `DART_API_KEY`가 없어야 한다
- 개인정보와 민감 정보는 DB에 저장하지 않는다
- GPS 같은 민감 정보는 어떤 테이블에도 저장하지 않는다

### GitHub Actions 기준
- 워크플로 파일: `.github/workflows/daily-market-refresh.yml`
- 원격 저장소: `gotbang/antgravity_sy`
- 브랜치 기준: `origin/master`
- 액션 버전: `actions/checkout@v5`, `actions/setup-python@v6`
- 필수 시크릿 사전검사 포함
- 스케줄: `0 22 * * 0-4`
  - GitHub UTC 기준
  - 한국 기준 월~금 오전 7시
- 실행 명령: `python backend/scripts/daily_refresh.py --phase ${{ github.event.inputs.phase || 'all' }}`

## 5. 품질 게이트

### 핵심 기준
- freshness: `20시간`
- 대표 US 종목: `AAPL`, `TSLA`
- 대표 KR 종목: `000660.KS`
- empty summary overwrite 금지
- 검색 정렬 우선순위 유지
- 브라우저 단계 라이브 폴백 금지
- 가격이 없어도 카드 빈칸 금지
- 활동반경은 `1.5% ~ 6.0%` 범위를 벗어나면 안 된다
- 오늘 탭은 로드 실패 시 가짜 리스크 숫자를 유지하면 안 된다

### 현재 완료된 검증 항목
- [X] `v_stock_detail_latest` 신규 필드 계약 반영
- [X] `price_status`가 `live | fallback | missing`으로 구분됨
- [X] fallback price payload 생성
- [X] 활동반경 계산 정책 테스트 추가
- [X] 카드가 `가격 준비중` 상태를 렌더함
- [X] 오늘 탭 placeholder 숫자 제거

### 검증 명령 기준
- 프론트
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
- 백엔드
  - `python -m pytest backend/tests/test_public_views_contract.py backend/tests/test_cache_freshness_gate.py backend/tests/test_direct_read_quality_gate.py backend/tests/test_search_rank_contract.py backend/tests/test_legacy_read_fallback_contract.py backend/tests/test_daily_refresh.py backend/tests/test_market_ingestion_smoke.py backend/tests/test_sensitive_data_guard.py backend/tests/test_activity_radius_policy.py`

## 6. rollback-only 레거시 기준

### 레거시 읽기 경로
- `/api/market-summary`
- `/api/stocks/search`
- `/api/stocks/{symbol}`

### 현재 해석
- 위 세 경로는 신규 주 경로가 아니다.
- 프론트 런타임은 이 경로들에 의존하지 않는다.
- 운영상 문제 발생 시 임시 되돌림 후보로만 남겨 둔다.

### 롤백 트리거
- 오늘 탭이 실제 데이터 대신 잘못된 기본값을 반복 노출할 때
- `price_status = missing` 종목이 체감상 급증해 카드 탐색성이 무너질 때
- 활동반경 계산값이 범위를 벗어나거나 의미 없는 값으로 반복될 때
- 브라우저가 원본 테이블이나 금지된 relation을 직접 조회할 때

## 7. 남은 리스크

### 적재 품질
- KR는 Yahoo chart fallback으로 보완됐지만 `PyKRX` 경로 안정성은 여전히 리스크다.
- US는 `yfinance`의 `unable to open database file` 문제가 간헐적으로 다시 날 수 있다.
- 이번 변경은 가격 공백을 줄이고 상태를 명확히 보여주지만, 전종목 가격 보장을 의미하지는 않는다.

### 지표 해석
- 활동반경은 투자 추천이 아니라 UI용 리스크 가이드다.
- 추후 사용자 피드백에 따라 가중치와 문구는 조정될 수 있다.

## 8. 문서 기준 정리

### 현재 기준 문서
- `docs/plan.md`
  - 운영 기준, 가격 상태 정책, 활동반경 정책
- `docs/PRD.md`
  - 사용자 가치와 수용 기준
- `spec/supabase-direct-read.md`
  - 공개 뷰와 카드 계약
- `docs/task.md`
  - 기존 direct-read 완료 + 후속 개선 작업 완료 상태
- `research.md`, `docs/research.md`
  - 문제 원인, 해결 방향, 남은 리스크
