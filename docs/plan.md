# AntGravity Supabase 직결 검토 plan

## 작성시각
2026-03-22 11:41:24 KST

## 1. 문서 목적
이 문서는 AntGravity의 주식 읽기 경로를 `정적 프론트 + Supabase 직결` 구조로 전환할 수 있는지 검토하고, 전환한다면 어떤 계약과 순서로 진행할지 결정하는 문서다. 현재 구현 기준과 후속 전환 계획을 함께 다루되, 현재 사실과 계획, 컷오버 조건이 섞이지 않게 분리해서 적는다.

이번 검토 범위는 주식 읽기 경로 직결 전환만 대상이다.
- 오늘 탭 요약
- 검색 결과 리스트
- 종목 상세 카드

## 2. 현재 구현 기준 스냅샷

### 현재 런타임 구조
- 프론트 엔트리는 정적 `index.html`이다.
- 브라우저는 Supabase를 직접 읽지 않고 FastAPI `/api/...` 경로를 호출한다.
- 앱 서버 엔트리는 `backend/main.py`다.
- 데이터 저장소는 Supabase 테이블 `ticker_universe`, `market_snapshot_daily`, `fundamentals_cache`, `market_summary_cache`다.
- 배치 적재는 `backend/scripts/daily_refresh.py`가 맡는다.

### 현재 사용자 흐름
- 로비 화면에는 부동산, 주식, 코인 3개 모드 카드가 있다.
- 주식 모드로 들어가면 `여왕의 지시`, `먹이 탐색`, `생존 일지` 3탭이 보인다.
- 오늘 탭은 `/api/market-summary` 응답을 받아 시장 기분, 공포탐욕 점수, 상승/하락 비중, AI 요약을 갱신한다.
- 먹이 탐색 탭은 로드시 `AAPL`, `TSLA`를 각각 카드 1, 카드 2에 채운다.
- 검색은 Enter와 버튼 클릭을 지원하지만 결과 리스트는 없고 첫 결과만 카드 1에 주입한다.
- 생존 일지 탭은 감정 선택과 텍스트 입력 UI만 있고 저장/복원은 없다.

### 현재 데이터 흐름
- `GET /api/market-summary`
  - `market_summary_cache.home`을 읽는다.
  - 캐시가 없고 summary 라이브 폴백이 허용되지 않으면 `503`이 가능하다.
- `GET /api/stocks/search`
  - `market_summary_cache.search:{query}`를 먼저 읽고, 없으면 `ticker_universe`를 `symbol/name ilike`로 직접 조회한다.
- `GET /api/stocks/{symbol}`
  - `fundamentals_cache`, `market_snapshot_daily`, `ticker_universe`를 조합한다.
  - snapshot이 없고 KR 종목이면 Yahoo chart API 가격 폴백을 시도한다.
- `GET /api/market/trending`
  - `market_summary_cache.trending`을 읽고, 없으면 빈 리스트를 반환할 수 있다.

### 현재 운영/보안 구조
- 브라우저는 현재 Supabase 키를 직접 쓰지 않는다.
- `SUPABASE_SERVICE_ROLE_KEY`와 `DART_API_KEY`는 백엔드/배치에서만 쓴다.
- CORS 허용 origin은 `5173`, `8080`, `5500` 계열 localhost 주소를 포함한다.
- 캐시 정책은 가격 폴백만 허용하고 요약/펀더멘털 폴백은 막는다.

### 현재 테스트 수준
- API 존재 여부와 폴백 정책을 보는 백엔드 테스트가 있다.
- `test_daily_refresh.py`, `test_market_ingestion_smoke.py`, `test_sensitive_data_guard.py`는 아직 placeholder다.
- 프론트 테스트는 `toHomeCardData()` 매핑 1건만 검증한다.
- 저장소 루트에 `package.json`이 없어 `pnpm lint`, `pnpm typecheck`를 현재 상태 그대로는 실행할 수 없다.

### 현재 문서/프로젝트 부채
- `docs/PRD.md`가 없다.
- `spec/` 디렉터리가 없다.
- 문서 일부는 한동안 `Supabase 직결` 목표 상태를 현재 구현처럼 서술해왔다.
- AGENTS 기준 명령과 실제 저장소 실행 경로가 완전히 맞물리진 않는다.

## 3. 직결 검토 범위와 비범위

### 이번 전환 범위
- 오늘 탭 요약 조회
- 검색 결과 리스트 조회
- 종목 상세 카드 조회

### 이번 전환 비범위
- 트렌딩 UI
- 생존 일지 저장
- 로그인/계정
- 배치 적재 제거
- 실시간 시세 스트리밍

### 보류 항목
- 트렌딩은 현재 API와 캐시는 존재하지만 UI가 없으므로 이번 직결 범위에서는 제외하고 보류로 명시한다.

## 4. 목표 아키텍처

### 목표 구조
- 프론트는 정적 `index.html` 중심 구조를 유지한다.
- 브라우저는 Supabase 공개 뷰 3개를 직접 조회한다.
- FastAPI 읽기 경로는 제거 후보로 본다.
- 배치 적재와 데이터 저장 구조는 유지한다.

### 전환 원칙
- 전환 방식은 `일괄 전환`으로 간다.
- 폴백 원칙은 `배치 품질 우선`이다.
- 브라우저 단계의 추가 라이브 폴백은 두지 않는다.
- 브라우저는 공개 뷰 3개만 읽는다.

### 대상 뷰
- `v_home_summary`
- `v_stock_search`
- `v_stock_detail_latest`

## 5. 캐시/적재 계획

### 목적
Supabase 직결 구조에서는 브라우저가 FastAPI의 조회 보정이나 가격 폴백을 거치지 않으므로, 화면 품질이 곧 적재 품질과 캐시 품질에 직접 연결된다. 이번 전환에서는 브라우저 단계의 임시 보정보다 배치 적재 결과의 일관성과 뷰 품질을 우선한다.

### Source of Truth
- 종목 마스터 원본: `ticker_universe`
- 일별 시세 원본: `market_snapshot_daily`
- 종목 상세 캐시: `fundamentals_cache`
- 홈 요약 캐시: `market_summary_cache`

직결 이후 브라우저는 원본 테이블을 직접 읽지 않고 아래 읽기 전용 뷰만 조회한다.
- `v_home_summary`
- `v_stock_search`
- `v_stock_detail_latest`

### 적재 파이프라인 유지 원칙
직결 전환 후에도 적재 파이프라인은 유지한다. 제거 대상은 읽기용 FastAPI 경로이며, 데이터 생산 경로는 그대로 남긴다.

현재 기준 적재 순서는 아래와 같다.
1. KR/US 유니버스를 수집해 `ticker_universe`에 upsert한다.
2. KR snapshot과 US snapshot을 수집해 `market_snapshot_daily`에 upsert한다.
3. snapshot 기반 종목 상세 캐시를 생성해 `fundamentals_cache`에 upsert한다.
4. KR 일부 종목의 재무/요약 데이터를 `fundamentals_cache`에 보강 저장한다.
5. 전체 snapshot 기준 시장 요약을 계산해 `market_summary_cache`의 `home` 키에 저장한다.
6. 일부 snapshot을 `market_summary_cache`의 `trending` 키에 저장한다.

### 뷰별 데이터 공급 계획
- `v_home_summary`
  - 공급원: `market_summary_cache`
  - 조회 기준: `cache_key = 'home'`
  - 역할: 오늘 탭 단일 행 공급
- `v_stock_search`
  - 공급원: `ticker_universe`
  - 역할: 검색 결과 리스트 공급
- `v_stock_detail_latest`
  - 공급원:
    - `market_snapshot_daily`
    - `ticker_universe`
    - `fundamentals_cache`
  - 역할: 카드용 최신 종목 상세 공급

### Freshness 기준
- 기본 freshness 기준은 현재 캐시 정책과 맞춰 `20시간`으로 고정한다.
- `market_summary_cache.home`과 `fundamentals_cache`는 `fetched_at` 기준 20시간 이내 데이터를 정상 범위로 본다.
- `market_snapshot_daily`는 종목별 최신 거래일 row가 존재해야 정상으로 본다.
- 브라우저는 stale 데이터를 별도 라이브 조회로 보정하지 않는다.
- stale 데이터가 보이면 브라우저 문제가 아니라 적재 실패 또는 배치 지연 문제로 분류한다.
- 현재 단계에서는 장중 실시간 적재를 도입하지 않는다.

### 적재 성공 기준
직결 구조에서 적재 성공은 단순히 배치가 끝나는 것이 아니라, 아래 조건을 만족해야 한다.
- `ticker_universe`에 검색 가능한 KR/US 주요 종목이 존재한다.
- `market_snapshot_daily`에 대표 US 종목 `AAPL`, `TSLA` 최신 row가 존재한다.
- `market_snapshot_daily`에 대표 KR 종목 `000660.KS` 최신 row가 존재한다.
- `market_summary_cache.home`이 빈 snapshot 기준 기본값이 아니라 실제 snapshot 집계 결과를 담고 있다.
- `v_stock_detail_latest`가 대표 종목 3개를 snapshot 기반으로 반환할 수 있다.

### 실패 처리 원칙
- `market_summary_cache.home`
  - snapshot 입력이 비정상이면 기존 정상값을 덮어쓰지 않는다.
  - 빈 입력으로 계산한 기본 summary를 정상 데이터처럼 승격하지 않는다.
- `market_snapshot_daily`
  - KR/US 중 한쪽 적재가 실패해도 반대쪽 정상 데이터는 유지한다.
  - 단, 대표 종목 품질 게이트를 만족하지 못하면 직결 컷오버는 막는다.
- `fundamentals_cache`
  - 재무/요약 보강 실패는 허용한다.
  - 하지만 시세 snapshot 자체가 비어 있거나 깨지는 상태는 허용하지 않는다.
- 브라우저 직결 후에는 KR Yahoo chart API 같은 추가 라이브 폴백을 두지 않는다.

### 컷오버 전 데이터 품질 게이트
아래 조건을 모두 만족할 때만 직결 구조로 일괄 전환한다.
- `market_summary_cache.home`이 최근 20시간 내 정상값으로 갱신돼 있다.
- 대표 US 종목 `AAPL`, `TSLA`가 `v_stock_detail_latest`에서 정상 조회된다.
- 대표 KR 종목 `000660.KS`가 `v_stock_detail_latest`에서 정상 조회된다.
- `v_stock_search`에서 `삼성`, `하이닉스`, `AAPL` 검색 시 의미 있는 결과가 상단에 노출된다.
- `price_source`가 대표 종목 기준으로 snapshot 기반인지 설명 가능하다.
- 브라우저가 추가 서버 폴백 없이도 기본 진입 화면을 정상 렌더한다.

### 직결 이후 운영 원칙
- 브라우저는 읽기 전용 뷰만 조회한다.
- 원본 테이블 직접 조회는 금지한다.
- stale 데이터, summary 품질 저하, 대표 종목 누락은 프론트 이슈가 아니라 적재/캐시 품질 이슈로 다룬다.
- 트렌딩 데이터는 적재는 유지하되, 현재 UI가 없으므로 이번 직결 범위에서는 보류한다.
- FastAPI 읽기 경로는 컷오버 검증 완료 전까지 rollback-only 레거시 백업 경로로 남길 수 있지만, 프론트 런타임 의존에서는 제거한다.

### 롤백 기준
직결 이후 아래 중 하나라도 발생하면 FastAPI 읽기 경로 유지 또는 롤백을 검토한다.
- 오늘 탭 요약이 기본값 수준으로 반복 노출된다.
- `000660.KS`가 snapshot 없이 빈 값으로 자주 떨어진다.
- 대표 US 종목 `AAPL`, `TSLA`가 20시간 이내 적재 기준으로 안정 조회되지 않는다.
- 검색 품질이 현재 API 기반 검색보다 명확히 나빠진다.
- stale 데이터 노출을 운영적으로 통제할 수 없다.

### 기본 가정
- 전환 전략은 `일괄 전환`으로 간다.
- 브라우저는 `SUPABASE_ANON_KEY`만 사용한다.
- `SUPABASE_SERVICE_ROLE_KEY`와 `DART_API_KEY`는 계속 배치/관리 전용이다.
- 브라우저 단계의 라이브 폴백은 두지 않는다.
- 화면 품질은 적재 품질과 뷰 품질로 확보한다.

## 6. RLS/공개 뷰 권한 계획

### 기본 원칙
- 브라우저는 원본 테이블을 직접 조회하지 않는다.
- 브라우저가 읽는 공개 surface는 읽기 전용 뷰 3개로 제한한다.
- 배치와 관리 작업만 원본 테이블에 접근한다.
- 공개 계약은 “RLS로 원본 차단 + 공개 뷰에만 select grant” 조합으로 고정한다.

### 권한 주체
- `anon`
  - 정적 프론트 런타임 전용
  - 공개 뷰 read만 허용
- `authenticated`
  - 현재 로그인 기능은 없지만 권한 정책은 `anon`과 동일하게 둔다.
  - 공개 뷰 read만 허용
- `service_role`
  - 배치 적재, 관리, 마이그레이션 전용
  - 원본 테이블 read/write 유지

### 원본 테이블 정책
대상:
- `ticker_universe`
- `market_snapshot_daily`
- `fundamentals_cache`
- `market_summary_cache`

원칙:
- 원본 테이블에는 RLS를 활성화한다.
- `anon`, `authenticated`에는 원본 테이블 `select` 정책을 만들지 않는다.
- `insert`, `update`, `delete`는 브라우저 역할에 모두 금지한다.
- 적재는 계속 `service_role` 경로만 사용한다.

### 공개 뷰 정책
대상:
- `v_home_summary`
- `v_stock_search`
- `v_stock_detail_latest`

원칙:
- 공개 뷰에는 `anon`, `authenticated`에 대해 `select`만 허용한다.
- 공개 뷰에는 `insert`, `update`, `delete` 권한을 주지 않는다.
- 공개 뷰는 브라우저 계약이므로 안전한 컬럼만 노출한다.
- 공개 뷰에 내부 운영용 컬럼은 넣지 않는다.

공개 금지 컬럼:
- 원본 `payload` 전체
- `fetched_at`
- 내부 디버깅용 메타데이터
- 배치 실행 상태를 직접 드러내는 운영 컬럼
- 시크릿, 키, 사용자 식별 정보, 민감 정보

### 공개 스키마 원칙
- 공개 읽기 surface는 뷰 3개만 유지한다.
- 브라우저는 이 3개 뷰 외의 relation 이름을 알 필요가 없게 만든다.
- 뷰 이름과 컬럼 이름이 곧 프론트 계약이다.
- SQL 레이어 컬럼명은 `snake_case`로 고정한다.
- 프론트는 adapter에서 현재 UI가 기대하는 camelCase 형태로 변환한다.

### 배치/관리 경로 원칙
- `daily_refresh.py`는 계속 `service_role`을 사용한다.
- 배치가 갱신하는 대상은 원본 테이블과 캐시 테이블이다.
- 공개 뷰는 배치 결과를 읽기 쉽게 노출하는 용도지, 적재 대상이 아니다.

### 컷오버 전 권한 검증 기준
- `anon`으로 원본 테이블 직접 조회가 실패해야 한다.
- `anon`으로 공개 뷰 3개 조회는 성공해야 한다.
- `service_role` 없이 적재 작업은 수행되지 않아야 한다.
- 브라우저 번들에는 `SUPABASE_ANON_KEY`만 존재해야 한다.
- `SUPABASE_SERVICE_ROLE_KEY`, `DART_API_KEY`는 브라우저에 노출되면 안 된다.

## 7. 뷰 스키마 계약 표

### 계약 원칙
- SQL 뷰는 `snake_case` 컬럼명을 사용한다.
- 프론트는 adapter에서 기존 UI 바인딩 형식으로 변환한다.
- 숫자 컬럼은 값이 없으면 `null`을 반환한다.
- 브라우저 직결 후 추가 라이브 폴백은 두지 않는다.
- 대표 KR 품질 게이트 종목은 `000660.KS`다.

### 1. `v_home_summary`
| 컬럼명 | 타입 | NULL 허용 | 공급원 | 설명 |
|------|------|-----------|--------|------|
| `updated_at` | `timestamptz` | 아니오 | `market_summary_cache.fetched_at` | 홈 요약 갱신 시각 |
| `market_mood` | `text` | 아니오 | `payload->>'marketMood'` | 시장 분위기 |
| `fear_greed_index` | `integer` | 아니오 | `payload->>'fearGreedIndex'` | 공포탐욕 점수 |
| `advancers` | `integer` | 아니오 | `payload->>'advancers'` | 상승 종목 수 |
| `decliners` | `integer` | 아니오 | `payload->>'decliners'` | 하락 종목 수 |
| `positive_ratio` | `numeric` | 아니오 | `payload->'sentimentMix'->>'positive'` | 상승 비율 |
| `negative_ratio` | `numeric` | 아니오 | `payload->'sentimentMix'->>'negative'` | 하락 비율 |
| `ai_summary` | `text` | 아니오 | `payload->>'aiSummary'` | 요약 문장 |

조회 규칙:
- `market_summary_cache`에서 `cache_key = 'home'` 1행만 노출한다.
- row가 없으면 브라우저는 기본 문구를 유지한다.
- 빈 snapshot 기준 기본 summary는 정상값으로 취급하지 않는다.

프론트 매핑:
- `market_mood` -> `marketMood`
- `fear_greed_index` -> `fearGreedIndex`
- `positive_ratio`, `negative_ratio` -> `sentimentMix.positive`, `sentimentMix.negative`
- `ai_summary` -> `aiSummary`

### 2. `v_stock_search`
| 컬럼명 | 타입 | NULL 허용 | 공급원 | 설명 |
|------|------|-----------|--------|------|
| `symbol` | `text` | 아니오 | `ticker_universe.symbol` | 종목 코드 |
| `name` | `text` | 아니오 | `coalesce(ticker_universe.name, symbol)` | 표시 이름 |
| `market` | `text` | 아니오 | `ticker_universe.market` | `KR` 또는 `US` |
| `sector` | `text` | 예 | `ticker_universe.sector` | 섹터 |
| `industry` | `text` | 예 | `ticker_universe.industry` | 산업 |
| `search_text` | `text` | 아니오 | 정규화 조합값 | 검색용 문자열 |

`search_text` 정의:
- `lower(symbol || ' ' || coalesce(name, ''))`

조회 규칙:
- 프론트는 `search_text ilike '%{query}%'`로 조회한다.
- 최대 8건만 사용한다.
- 검색어가 비면 조회하지 않는다.
- 정렬은 아래 우선순위로 고정한다.
  1. `symbol` exact match
  2. `symbol` prefix match
  3. `name` prefix match
  4. `search_text` contains match
  5. 동일 우선순위에서는 `market`, `name` 순

메모:
- 랭킹용 별도 score 컬럼은 이번 버전에서 만들지 않는다.
- 정렬 우선순위는 쿼리 레이어 또는 frontend adapter에서 동일하게 적용한다.

### 3. `v_stock_detail_latest`
| 컬럼명 | 타입 | NULL 허용 | 공급원 | 설명 |
|------|------|-----------|--------|------|
| `symbol` | `text` | 아니오 | `ticker_universe.symbol` | 종목 코드 |
| `name` | `text` | 아니오 | `coalesce(ticker_universe.name, symbol)` | 표시 이름 |
| `market` | `text` | 아니오 | `ticker_universe.market` | 시장 구분 |
| `snapshot_date` | `date` | 예 | 최신 `market_snapshot_daily.snapshot_date` | 최신 시세 날짜 |
| `price` | `numeric` | 예 | 최신 `market_snapshot_daily.close` | 현재 표시 가격 |
| `change_pct` | `numeric` | 예 | 최신 `market_snapshot_daily.change_pct` | 등락률 |
| `volume` | `bigint` | 예 | 최신 `market_snapshot_daily.volume` | 거래량 |
| `market_cap` | `numeric` | 예 | 최신 `market_snapshot_daily.market_cap` | 시가총액 |
| `per` | `numeric` | 예 | 최신 `market_snapshot_daily.per` | PER |
| `pbr` | `numeric` | 예 | 최신 `market_snapshot_daily.pbr` | PBR |
| `summary` | `text` | 예 | `fundamentals_cache.payload->>'aiSummary'` 우선, 없으면 `payload->>'summary'` | 종목 요약 |
| `price_source` | `text` | 예 | 최신 snapshot 존재 시 `'snapshot'` | 가격 출처 |

조회 규칙:
- 종목별 최신 snapshot 1건만 연결한다.
- 기본 driving table은 `ticker_universe`다.
- snapshot이 없으면 row는 남기되 `snapshot_date`, `price`, `change_pct` 등 시세 필드는 `null`로 반환한다.
- 브라우저는 이 상태를 그대로 표시하고 추가 라이브 폴백을 하지 않는다.
- 직결 컷오버 전 품질 게이트는 아래 3종목으로 본다.
  - `AAPL`
  - `TSLA`
  - `000660.KS`

프론트 매핑:
- `change_pct` -> 현재 카드 change 표시
- `market` -> `KRW`/`USD` 포맷 분기
- `price_source`는 운영 점검용으로만 쓰고 기본 UI에는 노출하지 않는다.

## 8. 프론트 조회 전환 순서

### 전환 원칙
- 전환 방식은 `일괄 전환`으로 간다.
- 이번 전환 대상은 읽기 경로 3개다.
  - 오늘 탭 요약
  - 검색 결과 리스트
  - 종목 상세 카드
- 브라우저는 전환 완료 후 `/api/market-summary`, `/api/stocks/search`, `/api/stocks/{symbol}`를 더 이상 호출하지 않는다.
- 트렌딩은 이번 전환 범위에 포함하지 않는다.
- 브라우저 단계의 라이브 폴백은 두지 않는다.

### 사전 준비
전환 시작 전에 아래 조건이 먼저 준비돼 있어야 한다.
- `v_home_summary`, `v_stock_search`, `v_stock_detail_latest`가 생성돼 있다.
- `anon`으로 뷰 3개 조회가 가능하다.
- `anon`으로 원본 테이블 직접 조회는 불가능하다.
- 대표 종목 `AAPL`, `TSLA`, `000660.KS`가 `v_stock_detail_latest`에서 정상 반환된다.
- `market_summary_cache.home` 품질이 컷오버 가능한 수준으로 안정돼 있다.

### 1단계. Supabase 브라우저 읽기 레이어 추가
목표:
- 프론트가 FastAPI 대신 Supabase를 읽을 수 있는 최소 읽기 레이어를 먼저 만든다.

작업:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`를 프론트 런타임에서 읽는다.
- 기존 `fetchJson('/api/...')` 기반 helper를 대체할 Supabase query helper를 만든다.
- helper는 아래 3개 조회만 지원한다.
  - 홈 요약 1건 조회
  - 검색 결과 조회
  - 종목 상세 단건 조회

완료 기준:
- 브라우저에서 뷰 3개를 개별 조회할 수 있다.
- helper 레벨에서 컬럼명을 UI가 쓰는 형식으로 변환할 수 있다.

### 2단계. 오늘 탭 조회 전환
목표:
- `/api/market-summary` 의존을 제거한다.

작업:
- 현재 오늘 탭 바인딩 함수가 `v_home_summary`를 직접 읽도록 바꾼다.
- SQL `snake_case` 응답을 현재 화면이 기대하는 값으로 adapter에서 변환한다.
- row 없음, stale, 조회 실패 상태를 현재 기본 UI와 충돌 없이 처리한다.

표시 규칙:
- 정상 row가 있으면 현재와 같은 위치에 값만 바인딩한다.
- row가 없으면 기본 문구와 기본 수치를 유지한다.
- 조회 실패는 콘솔 기록만 남기고 화면 기본값을 깨지 않는다.

완료 기준:
- 오늘 탭 진입 시 `/api/market-summary` 호출이 사라진다.
- 화면이 `v_home_summary` 결과로 동일하게 렌더된다.

### 3단계. 기본 카드 조회 전환
목표:
- `/api/stocks/{symbol}` 의존 중 기본 카드 2개부터 제거한다.

작업:
- 초기 로드시 `AAPL`, `TSLA`를 `v_stock_detail_latest`에서 조회한다.
- 카드 1, 카드 2를 같은 adapter를 통해 렌더한다.
- `market` 값으로 `KRW`/`USD` 포맷 분기를 유지한다.
- `price`, `change_pct`가 `null`이면 현재 UI에서 `-` 또는 빈 값 처리 규칙을 적용한다.

표시 규칙:
- 카드별 개별 실패를 허용한다.
- 카드 1 실패가 카드 2 렌더를 막지 않는다.
- 카드 2 실패가 카드 1 렌더를 막지 않는다.

완료 기준:
- 초기 카드 로드시 `/api/stocks/AAPL`, `/api/stocks/TSLA` 호출이 사라진다.
- 기본 카드 2개가 `v_stock_detail_latest` 기반으로 렌더된다.

### 4단계. 검색 조회 전환
목표:
- `/api/stocks/search`와 `/api/stocks/{symbol}` 기반 검색 흐름을 전부 제거한다.

작업:
- 검색 input에 150~250ms 디바운스를 둔다.
- 입력 시 `v_stock_search`를 조회한다.
- 결과 리스트를 검색창 아래 드롭다운으로 렌더한다.
- 항목 선택 시 `v_stock_detail_latest` 단건 조회로 카드 1을 갱신한다.

입력 규칙:
- 검색어가 비면 조회하지 않는다.
- 검색어가 비면 결과 리스트를 닫는다.
- 최대 8개 결과만 노출한다.

선택 규칙:
- 클릭: 해당 종목 선택
- Enter: 하이라이트 우선, 없으면 첫 결과 선택
- ArrowDown/ArrowUp: 하이라이트 이동
- Escape: 리스트 닫기

상태 규칙:
- 로딩 상태 표시
- 결과 없음 상태 표시
- 조회 실패 상태 표시
- 세 상태는 서로 다른 메시지로 구분한다.

완료 기준:
- 검색 시 `/api/stocks/search` 호출이 사라진다.
- 선택 시 `/api/stocks/{symbol}` 호출이 사라진다.
- 검색 리스트 UX가 기존 첫 결과 자동 주입을 대체한다.

### 5단계. API 의존 제거 확인
목표:
- 프론트 런타임에서 읽기용 FastAPI 의존이 완전히 빠졌는지 확인한다.

확인 대상:
- 오늘 탭
- 기본 카드 2개
- 검색 결과
- 검색 선택 후 카드 1 갱신

완료 기준:
- 브라우저 네트워크에서 아래 호출이 0회다.
  - `/api/market-summary`
  - `/api/stocks/search`
  - `/api/stocks/{symbol}`
- 브라우저는 공개 뷰 3개만 조회한다.

### 6단계. 레거시 경로 재분류
목표:
- 프론트가 더 이상 안 쓰는 읽기용 FastAPI 경로를 레거시로 재분류한다.

원칙:
- 바로 삭제하지 않아도 된다.
- 먼저 “프론트 미사용” 상태를 확인한 뒤 레거시 표시를 한다.
- 배치/적재 코드는 그대로 유지한다.

대상:
- `/api/market-summary`
- `/api/stocks/search`
- `/api/stocks/{symbol}`

보류:
- `/api/market/trending`
- 트렌딩 UI
- 생존 일지 저장 기능

## 9. 컷오버 체크리스트

### A. 데이터/뷰 준비
- [ ] `v_home_summary`가 생성돼 있다.
- [ ] `v_stock_search`가 생성돼 있다.
- [ ] `v_stock_detail_latest`가 생성돼 있다.
- [ ] `anon`으로 뷰 3개 조회가 가능하다.
- [ ] `anon`으로 원본 테이블 직접 조회는 불가능하다.
- [ ] 대표 US 종목 `AAPL`, `TSLA`가 `v_stock_detail_latest`에서 정상 조회된다.
- [ ] 대표 KR 종목 `000660.KS`가 `v_stock_detail_latest`에서 정상 조회된다.
- [ ] `market_summary_cache.home`가 최근 20시간 이내 정상값으로 갱신돼 있다.

### B. 프론트 기능 전환
- [ ] 오늘 탭이 `v_home_summary`로 렌더된다.
- [ ] 기본 카드 1이 `AAPL` 직결 조회로 렌더된다.
- [ ] 기본 카드 2가 `TSLA` 직결 조회로 렌더된다.
- [ ] 검색 입력 디바운스가 적용돼 있다.
- [ ] 검색 결과 리스트가 최대 8건까지 노출된다.
- [ ] 클릭 선택이 동작한다.
- [ ] Enter 선택이 동작한다.
- [ ] 방향키 이동이 동작한다.
- [ ] Escape 닫기가 동작한다.
- [ ] 결과 없음 상태가 표시된다.
- [ ] 조회 실패 상태가 표시된다.

### C. 네트워크/권한 검증
- [ ] 브라우저 네트워크에서 `/api/market-summary` 호출이 없다.
- [ ] 브라우저 네트워크에서 `/api/stocks/search` 호출이 없다.
- [ ] 브라우저 네트워크에서 `/api/stocks/{symbol}` 호출이 없다.
- [ ] 브라우저는 공개 뷰 3개만 조회한다.
- [ ] 브라우저 번들에 `SUPABASE_SERVICE_ROLE_KEY`가 없다.
- [ ] 브라우저 번들에 `DART_API_KEY`가 없다.
- [ ] 브라우저 런타임에는 `SUPABASE_ANON_KEY`만 사용된다.

### D. 화면 품질 검증
- [ ] 오늘 탭의 시장 분위기, 공포탐욕 점수, 상승/하락 수치가 정상 표시된다.
- [ ] 기본 카드 가격과 등락률이 정상 표시된다.
- [ ] KR 종목 선택 시 `KRW` 포맷이 유지된다.
- [ ] US 종목 선택 시 `USD` 포맷이 유지된다.
- [ ] `price = null`일 때 화면이 깨지지 않는다.
- [ ] `summary = null`이어도 카드 렌더가 깨지지 않는다.

### E. 품질 게이트
- [ ] `market_summary_cache.home`가 빈 snapshot 기본값으로 반복 저장되지 않는다.
- [ ] `000660.KS`가 snapshot 기반으로 안정 조회된다.
- [ ] `AAPL`, `TSLA`가 snapshot 기반으로 안정 조회된다.
- [ ] 검색 품질이 기존 API 기반 검색보다 나빠지지 않는다.
- [ ] 브라우저 단계 라이브 폴백 없이도 기본 사용자 흐름이 유지된다.

### F. 보류 항목 확인
- [ ] 트렌딩은 이번 컷오버 범위 밖이라는 점이 문서에 남아 있다.
- [ ] `/api/market/trending`과 트렌딩 UI는 이번 전환에서 건드리지 않는다.
- [ ] 생존 일지 저장 기능은 이번 전환 범위 밖이다.

### G. 컷오버 완료 선언 조건
아래를 모두 만족할 때만 컷오버 완료로 본다.
- [ ] 읽기용 주식 기능 3개가 모두 Supabase 직결로 동작한다.
- [ ] 브라우저에서 기존 읽기용 FastAPI 호출이 0회다.
- [ ] 대표 KR/US 종목 품질 게이트를 통과한다.
- [ ] 공개 뷰/RLS/권한 검증이 끝났다.
- [ ] 보류 항목과 제외 범위가 문서와 실제 구현에서 일치한다.

## 10. 리스크/롤백 계획

### 목적
Supabase 직결 전환은 읽기 경로를 단순화하는 대신, 브라우저가 적재 품질과 공개 뷰 품질에 직접 의존하게 만든다. 따라서 이번 전환은 성공 기준뿐 아니라 중단 기준과 되돌림 기준을 명확히 가진 상태로 진행해야 한다.

### 핵심 리스크
- 적재 품질 리스크
  - `market_summary_cache.home`가 빈 snapshot 기준 기본값으로 다시 저장될 수 있다.
  - KR snapshot 적재가 불안정하면 대표 KR 종목 `000660.KS`가 빈 값 또는 약한 데이터로 노출될 수 있다.
- 검색 품질 리스크
  - 현재 API 검색보다 결과 정렬 품질이 떨어질 수 있다.
  - `삼성`, `하이닉스`, `AAPL` 같은 대표 검색어에서 기대 결과가 상단에 오지 않을 수 있다.
- 권한/보안 리스크
  - 공개 뷰 권한이 과하게 열리면 원본 데이터 노출 위험이 생긴다.
  - 프론트 번들에 `service_role` 문맥 값이 섞이면 즉시 실패다.
- UI 전환 리스크
  - 오늘 탭, 카드, 검색 리스트 중 일부만 직결로 바뀌고 일부가 FastAPI를 계속 보면 혼합 상태가 길어질 수 있다.
  - `null` 값 처리 규칙이 빠지면 가격/등락률/요약 표시가 깨질 수 있다.
- 운영 리스크
  - 배치가 늦거나 실패해도 브라우저는 라이브 폴백을 하지 않으므로 stale 데이터가 그대로 보일 수 있다.
  - 직결 후 장애가 나면 문제가 프론트인지 뷰인지 적재인지 빠르게 구분할 수 있어야 한다.

### 리스크별 대응 원칙
- 적재 품질 리스크 대응
  - 직결 전환 전 `market_summary_cache.home` 품질을 먼저 안정화한다.
  - 대표 종목 `AAPL`, `TSLA`, `000660.KS`를 품질 게이트로 고정한다.
  - snapshot 없는 상태를 브라우저 폴백으로 숨기지 않는다.
- 검색 품질 리스크 대응
  - `v_stock_search`는 컷오버 전에 대표 검색어 결과를 수동 검증한다.
  - 검색 품질이 현재 구조보다 나빠지면 검색 경로는 컷오버하지 않는다.
- 권한/보안 리스크 대응
  - 원본 테이블은 `anon` direct select 금지
  - 공개 뷰만 `anon` select 허용
  - 프론트 런타임 변수는 `SUPABASE_URL`, `SUPABASE_ANON_KEY`만 허용
- UI 전환 리스크 대응
  - 전환은 일괄 전환으로 가되, 화면별 검증은 오늘 탭 -> 기본 카드 -> 검색 순서로 체크한다.
  - 기존 FastAPI 읽기 경로는 즉시 삭제하지 않고 롤백 가능한 상태로 잠시 유지한다.
- 운영 리스크 대응
- stale 기준은 20시간으로 고정한다.
  - stale 또는 품질 저하가 보이면 적재/뷰 문제로 우선 분류한다.

### 컷오버 중단 기준
아래 중 하나라도 발생하면 직결 컷오버를 중단하고 FastAPI 읽기 경로를 유지한다.
- `v_home_summary`가 안정적으로 정상 row를 반환하지 못한다.
- `AAPL`, `TSLA`, `000660.KS` 중 하나라도 `v_stock_detail_latest`에서 반복적으로 빈 값 또는 비정상 값으로 나온다.
- 검색 결과 리스트 품질이 현재 API 검색보다 명확히 나쁘다.
- `anon`으로 원본 테이블 직접 조회가 가능하다.
- 브라우저 번들 또는 런타임에서 `SUPABASE_SERVICE_ROLE_KEY`, `DART_API_KEY` 흔적이 확인된다.
- 오늘 탭/카드/검색 중 하나라도 기존 기본 사용자 흐름을 깨뜨린다.

### 롤백 트리거
직결 배포 또는 로컬 컷오버 검증 이후 아래 조건이 발생하면 롤백한다.
- 오늘 탭이 기본값 수준으로 반복 노출된다.
- 대표 KR 종목 `000660.KS`가 snapshot 기반으로 안정 조회되지 않는다.
- 대표 US 종목 `AAPL`, `TSLA`가 20시간 이내 적재 기준으로 안정 조회되지 않는다.
- 검색 리스트가 열리지만 선택 결과가 카드 반영까지 안정적으로 이어지지 않는다.
- null 처리 누락으로 카드 또는 오늘 탭 UI가 깨진다.
- 브라우저가 뷰 외 relation을 직접 조회한다.
- 배치 지연이 발생했을 때 사용자 화면 품질 저하를 운영적으로 감당할 수 없다.

### 롤백 방식
이번 전환의 롤백은 기존 읽기용 FastAPI 경로로 프론트 의존을 되돌리는 것으로 정의한다.

롤백 순서:
1. 프론트 조회 helper를 Supabase 직결 경로에서 기존 `/api/...` 경로로 되돌린다.
2. 오늘 탭을 `/api/market-summary` 기반으로 되돌린다.
3. 기본 카드와 검색 상세를 `/api/stocks/{symbol}` 기반으로 되돌린다.
4. 검색 리스트가 이미 들어갔다면, 검색 결과 source만 `/api/stocks/search`로 되돌린다.
5. 공개 뷰와 RLS 정책은 유지할 수 있지만, 프론트가 더 이상 사용하지 않는 상태로 둔다.
6. FastAPI 읽기 경로가 정상 동작하는지 다시 검증한다.

### 롤백 후 유지 원칙
- 롤백은 실패가 아니라 보호 장치로 취급한다.
- 롤백 후에도 배치/적재 개선 작업은 계속 진행한다.
- 공개 뷰 설계와 권한 설계는 폐기하지 않고 후속 재시도 자산으로 남긴다.
- 재시도 전에는 실패 원인을 아래 3분류 중 하나로 명확히 남긴다.
  - 적재 품질 문제
  - 뷰 계약 문제
  - 프론트 상태 처리 문제

### 재시도 조건
롤백 이후 다시 직결을 시도하려면 아래를 만족해야 한다.
- 실패 원인이 문서화돼 있다.
- 같은 실패가 다시 나지 않도록 뷰/적재/UI 수정 사항이 확정돼 있다.
- 대표 종목 3개 품질 게이트를 다시 통과한다.
- 검색 품질 검증을 다시 통과한다.
- 보안/RLS 검증을 다시 통과한다.

### 기본 가정
- 이번 직결은 읽기 경로 전환만 다룬다.
- 배치 적재는 계속 유지한다.
- 브라우저 라이브 폴백은 도입하지 않는다.
- 롤백 기본 경로는 기존 FastAPI 읽기 API다.

## 11. 후속 작업 트랙

### 현재 구조 안정화 트랙
- `market_summary_cache.home` 품질 안정화
- KR snapshot 적재 안정화
- 대표 종목 품질 게이트 정기 점검

### 검색 UX 보강 트랙
- 검색 리스트 드롭다운 도입
- Enter/클릭/방향키/Escape 상태 정리
- 검색 정렬 품질 보강

### 직결 전환 트랙
- 공개 뷰 3개 생성
- RLS/권한 검증
- 프론트 직결 조회 helper 도입
- FastAPI 읽기 경로 의존 제거

### 레거시 정리 트랙
- 프론트 미사용 FastAPI 읽기 경로 레거시 재분류
- 트렌딩 보류 범위 재검토
- 배치와 앱 서버 역할 문서 분리

### 문서/테스트 부채 트랙
- `docs/PRD.md` 부재 정리
- `spec/` 부재 정리
- placeholder 테스트 보강
- 루트 실행 체계와 품질게이트 정리
