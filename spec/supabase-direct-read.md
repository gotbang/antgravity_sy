# Supabase Direct-Read Spec

## 작성시각
2026-03-22 13:55:50 KST

## 문서 목적
이 문서는 AntGravity 주식 모드의 direct-read 구현 계약을 현재 기준으로 고정한다. 공개 뷰, 프론트 바인딩, 품질 게이트, 보안 경계를 한 문서에서 바로 확인할 수 있게 정리한다.

## 1. 현재 계약 요약
- 브라우저는 Supabase 공개 뷰 3개만 직접 조회한다.
- 읽기용 FastAPI 경로는 rollback-only 레거시 경로다.
- 먹이 탐색 탭은 단일 카드 1장만 사용한다.
- freshness 기준은 `20시간`이다.

## 2. 런타임 계약

### 브라우저 런타임 값
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

### 금지 값
- `SUPABASE_SERVICE_ROLE_KEY`
- `DART_API_KEY`
- 배치/관리용 쓰기 권한 값

### 공개 env 공급 방식
- 루트 `.env` -> `src/config/public-env.generated.js`
- 명령
  - `pnpm run sync:public-env`
  - `pnpm run dev`

## 3. Source of Truth
- `ticker_universe`
  - 종목 마스터
- `market_snapshot_daily`
  - 최신 시세 원본
- `fundamentals_cache`
  - 종목 상세 요약/재무 캐시
- `market_summary_cache`
  - 홈 요약 캐시

## 4. 공개 뷰 계약

### `v_home_summary`
역할:
- 오늘 탭 단일 행 공급

주요 컬럼:
| 컬럼명 | 타입 | 설명 |
| --- | --- | --- |
| `updated_at` | `timestamptz` | 홈 요약 갱신 시각 |
| `market_mood` | `text` | 시장 분위기 |
| `fear_greed_index` | `integer` | 공포탐욕 점수 |
| `advancers` | `integer` | 상승 종목 수 |
| `decliners` | `integer` | 하락 종목 수 |
| `positive_ratio` | `numeric` | 상승 비율 |
| `negative_ratio` | `numeric` | 하락 비율 |
| `ai_summary` | `text` | AI 요약 문장 |

프론트 매핑:
- `market_mood` -> `marketMood`
- `fear_greed_index` -> `fearGreedIndex`
- `positive_ratio`, `negative_ratio` -> `sentimentMix`
- `ai_summary` -> `aiSummary`

동작 규칙:
- `cache_key = 'home'` 기준 단일 행을 사용한다
- row가 없거나 조회 실패면 화면은 기본 문구를 유지한다

### `v_stock_search`
역할:
- 검색 결과 리스트 공급

주요 컬럼:
| 컬럼명 | 타입 | 설명 |
| --- | --- | --- |
| `symbol` | `text` | 종목 코드 |
| `name` | `text` | 표시 이름 |
| `market` | `text` | `KR` 또는 `US` |
| `sector` | `text` | 섹터 |
| `industry` | `text` | 산업 |
| `search_text` | `text` | 검색용 정규화 문자열 |

검색 규칙:
- 검색어가 비면 조회하지 않는다
- 최대 8건만 노출한다
- 정렬 우선순위
  1. `symbol` exact match
  2. `symbol` prefix match
  3. `name` prefix match
  4. `search_text` contains match

### `v_stock_detail_latest`
역할:
- 카드용 최신 종목 상세 공급

주요 컬럼:
| 컬럼명 | 타입 | 설명 |
| --- | --- | --- |
| `symbol` | `text` | 종목 코드 |
| `name` | `text` | 표시 이름 |
| `market` | `text` | 시장 구분 |
| `snapshot_date` | `date` | 최신 시세 날짜 |
| `price` | `numeric` | 표시 가격 |
| `change_pct` | `numeric` | 등락률 |
| `volume` | `bigint` | 거래량 |
| `market_cap` | `numeric` | 시가총액 |
| `per` | `numeric` | PER |
| `pbr` | `numeric` | PBR |
| `summary` | `text` | 종목 요약 |
| `price_source` | `text` | 가격 출처 |

동작 규칙:
- 종목별 최신 snapshot 1건 기준
- 기본 카드 심볼은 `AAPL`
- 검색 선택 후에도 같은 카드 1장을 교체한다
- snapshot이 없으면 시세 필드는 `null`일 수 있다
- 브라우저는 추가 라이브 폴백을 하지 않는다

프론트 표시 규칙:
- `market = KR`면 `KRW`
- `market = US`면 `USD`
- `price`, `summary`가 `null`이어도 렌더가 깨지면 안 된다

## 5. 프론트 상호작용 계약

### 오늘 탭
- direct-read 결과로만 렌더한다
- legacy `/api/market-summary`에 의존하지 않는다

### 먹이 탐색
- 기본 카드 한 장만 노출한다
- 초기 로드는 `AAPL`
- 검색 결과 선택 시 같은 카드 한 장을 갱신한다

### 검색 상호작용
- 클릭 선택 지원
- Enter 선택 지원
- ArrowUp/ArrowDown 하이라이트 이동 지원
- Escape 닫기 지원
- 로딩/결과 없음/오류 상태를 구분한다

## 6. 품질 게이트
- freshness `20시간`
- 대표 종목 `AAPL`, `TSLA`, `000660.KS`
- empty summary overwrite 금지
- `000660.KS`는 snapshot 기반으로 정상 조회돼야 한다
- 브라우저는 공개 뷰 3개만 조회해야 한다

## 7. 권한과 보안 계약
- 원본 테이블은 `anon`, `authenticated` direct select 금지
- 공개 뷰 3개에만 `anon`, `authenticated` select 허용
- 브라우저 번들에는 공개 env만 존재해야 한다
- 사용자 개인정보와 민감 정보는 저장하지 않는다
- GPS 정보는 어떤 저장 경로에도 넣지 않는다

## 8. 검증 명령

### 프론트
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`

### 백엔드
- `python -m pytest backend/tests/test_public_views_contract.py backend/tests/test_cache_freshness_gate.py backend/tests/test_direct_read_quality_gate.py backend/tests/test_search_rank_contract.py backend/tests/test_legacy_read_fallback_contract.py backend/tests/test_daily_refresh.py backend/tests/test_market_ingestion_smoke.py backend/tests/test_sensitive_data_guard.py`

## 9. rollback 계약

### rollback-only 레거시 경로
- `/api/market-summary`
- `/api/stocks/search`
- `/api/stocks/{symbol}`

### 해석
- 위 세 경로는 신규 주 경로가 아니다
- direct-read 운영 장애 시 임시 복귀 경로로만 취급한다

## 10. 현재 보류 범위
- 트렌딩 UI
- 생존 일지 저장/복원
- 로그인/계정
- 실시간 시세 스트리밍
