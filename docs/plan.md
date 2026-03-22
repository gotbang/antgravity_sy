# AntGravity Supabase direct-read 운영 plan

## 작성시각
2026-03-22 13:55:50 KST

## 문서 목적
이 문서는 더 이상 “직결 전환 가능 여부를 검토하는 초안”이 아니다. 현재 구현이 이미 `정적 HTML + Supabase direct-read + 배치 적재` 기준으로 동작한다는 전제 아래, 운영 기준, 품질 게이트, 롤백 조건, 남은 리스크를 한곳에 고정하는 기준 문서다.

## 1. 현재 기준 요약

### 현재 구조
- 프론트 엔트리는 정적 `index.html`이다.
- 브라우저는 `v_home_summary`, `v_stock_search`, `v_stock_detail_latest`를 direct-read 한다.
- 로컬 공개 env는 루트 `.env`에서 `src/config/public-env.generated.js`로 동기화한다.
- 배치 적재는 `backend/scripts/daily_refresh.py`가 맡는다.
- FastAPI 읽기 경로는 주 경로가 아니라 rollback-only 레거시 경로다.

### 현재 사용자 경험
- 로비에는 부동산, 주식, 코인 3개 모드 카드가 있다.
- 주식 모드에는 `여왕의 지시`, `먹이 탐색`, `생존 일지` 3탭이 있다.
- 오늘 탭은 `v_home_summary` 결과를 바인딩한다.
- 먹이 탐색 탭은 단일 종목 카드 1장만 사용하고 기본 심볼은 `AAPL`이다.
- 검색은 결과 리스트, 클릭, Enter, 방향키, Escape를 지원한다.
- 검색 결과를 고르면 같은 카드 1장이 선택 종목으로 교체된다.
- 생존 일지는 감정 선택과 텍스트 입력 UI만 있고 저장 기능은 아직 없다.

### 현재 검증 상태
- `docs/task.md` 기준 태스크 `45/45` 완료
- 대표 direct-read 호출 `200` 응답 확인
- 브라우저 실사용 검증 완료
- `pnpm lint`, `pnpm typecheck`, `pnpm test` 기준 통과 문맥 정리 완료
- 백엔드 direct-read 품질 게이트 문서화 완료

## 2. 범위와 비범위

### 현재 운영 범위
- 오늘 탭 요약 조회
- 종목 검색 결과 리스트 조회
- 선택 종목 상세 카드 조회
- direct-read 공개 뷰 3개 운영
- 배치 적재와 품질 게이트 운영
- rollback-only FastAPI 읽기 경로 유지

### 현재 비범위
- 트렌딩 UI 복구
- 생존 일지 저장/복원
- 로그인/계정
- 실시간 시세 스트리밍
- 브라우저 단계 라이브 폴백

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
- 먹이 탐색
  - 초기 단일 카드: `AAPL`
  - 검색 결과: `v_stock_search`
  - 선택 후 카드 갱신: `v_stock_detail_latest`
  - 가격 포맷: KR=`KRW`, US=`USD`
- 생존 일지
  - 입력 UI만 존재
  - 저장 기능은 범위 밖

### 배치 적재 순서
1. KR/US 유니버스를 수집해 `ticker_universe`에 upsert
2. KR/US snapshot을 수집해 `market_snapshot_daily`에 upsert
3. snapshot 기반 상세 캐시를 `fundamentals_cache`에 upsert
4. 일부 KR 종목 재무/요약을 `fundamentals_cache`에 보강
5. 시장 요약을 `market_summary_cache.home`에 저장
6. 일부 snapshot 기반 데이터를 `market_summary_cache.trending`에 저장

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
- 스케줄: 평일 `0 22 * * 1-5`
- 실행 명령: `python backend/scripts/daily_refresh.py --phase ${{ github.event.inputs.phase || 'all' }}`
- 현재 로컬 저장소에는 remote가 없어 최신 원격 반영 여부와 최근 run 성공 여부는 별도 확인이 필요하다

## 5. 품질 게이트

### 핵심 기준
- freshness: `20시간`
- 대표 US 종목: `AAPL`, `TSLA`
- 대표 KR 종목: `000660.KS`
- empty summary overwrite 금지
- 검색 정렬 우선순위 유지
- 브라우저 단계 라이브 폴백 금지

### 현재 완료된 검증 항목
- [X] `v_home_summary` direct-read 응답 확인
- [X] `v_stock_detail_latest?symbol=eq.AAPL` 응답 확인
- [X] `v_stock_detail_latest?symbol=eq.TSLA` 응답 확인
- [X] `v_stock_detail_latest?symbol=eq.000660.KS` 응답 확인
- [X] `v_stock_search?search_text=ilike.%하이닉스%` 응답 확인
- [X] 브라우저에서 오늘 탭 로드 확인
- [X] 브라우저에서 기본 단일 카드 로드 확인
- [X] 검색 결과 리스트와 선택 흐름 확인
- [X] `SK하이닉스 / 000660.KS / KR` 선택 후 가격 `₩1,007,000` 확인
- [X] 콘솔 에러 0개 확인
- [X] 공개 뷰 계약 테스트 문서화
- [X] freshness gate 문서화
- [X] direct-read quality gate 문서화
- [X] search rank contract 문서화
- [X] rollback-only 경로 검증 문서화

### 검증 명령 기준
- 프론트
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
- 백엔드
  - `python -m pytest backend/tests/test_public_views_contract.py backend/tests/test_cache_freshness_gate.py backend/tests/test_direct_read_quality_gate.py backend/tests/test_search_rank_contract.py backend/tests/test_legacy_read_fallback_contract.py backend/tests/test_daily_refresh.py backend/tests/test_market_ingestion_smoke.py backend/tests/test_sensitive_data_guard.py`

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
- 오늘 탭이 기본값 수준으로 반복 노출될 때
- `000660.KS`가 snapshot 없이 빈 값으로 반복 노출될 때
- `AAPL`, `TSLA`가 freshness 기준 안에서 안정 조회되지 않을 때
- 검색 결과 품질이 현재 direct-read 기준보다 명확히 나빠질 때
- 브라우저가 원본 테이블이나 금지된 relation을 직접 조회할 때
- 브라우저 번들에 시크릿 노출 흔적이 생길 때

### 롤백 순서
1. 프론트 조회 helper를 direct-read 경로에서 레거시 `/api/...` 경로로 되돌린다.
2. 오늘 탭을 `/api/market-summary`로 되돌린다.
3. 검색과 상세 조회를 `/api/stocks/search`, `/api/stocks/{symbol}`로 되돌린다.
4. 공개 뷰와 RLS는 유지하되 프론트 의존을 제거한 상태로 둔다.
5. 레거시 읽기 경로 정상 동작을 다시 검증한다.

## 7. 남은 리스크

### 적재 품질
- KR는 Yahoo chart fallback으로 보완됐지만 `PyKRX` 경로 안정성은 아직 리스크다.
- US는 `yfinance`의 `unable to open database file` 문제가 간헐적으로 다시 날 수 있다.

### 운영 확인
- GitHub Actions workflow 자체는 존재한다.
- 하지만 원격 최신 코드 반영 여부와 최근 성공 run 여부는 아직 로컬에서 확인하지 못했다.

### 워킹트리 관리
- 이번 문서 작업과 무관한 예전 변경이 워킹트리에 남아 있다.
- 다음 세션에서 정리 여부를 별도 판단해야 한다.

## 8. 문서 기준 정리

### 현재 기준 문서
- `memory.md`
  - 세션 인수인계와 현재 동작 요약
- `research.md`, `docs/research.md`
  - 현재 구현과 런타임 검증 결과
- `docs/PRD.md`
  - 제품 요구사항 현재 기준
- `spec/supabase-direct-read.md`
  - 공개 뷰와 direct-read 계약 기준
- `docs/quickstart.md`
  - 실제 실행 경로와 검증 경로
- `docs/task.md`
  - 태스크 이행 결과와 완료 상태

### 이번 문서 정리로 반영한 점
- `docs/PRD.md`와 `spec/` 부재 문맥은 제거한다.
- `전환 검토 중` 표현 대신 `구현 완료 후 운영 기준` 문맥으로 고정한다.
- 단일 카드 UI, direct-read 실동작, rollback-only 레거시 문맥을 현재 기준으로 통일한다.

## 9. 다음 문서 작업 우선순위
1. GitHub Actions 원격 검증 결과가 확보되면 운영가이드에 실측 결과를 추가한다.
2. US 적재 품질 이슈가 재발하면 원인과 대응을 `research.md`와 개발일지에 누적한다.
3. 생존 일지 저장 기능을 시작할 때는 현재 direct-read 문서와 분리된 새 요구사항 문서로 시작한다.
