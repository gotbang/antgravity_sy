# Supabase Direct-Read Spec

## 작성시각
2026-03-22 16:20:06 KST

## 문서 목적
이 문서는 AntGravity 주식 모드의 direct-read 구현 계약을 현재 기준으로 고정한다. 이번 갱신에서는 `v_stock_detail_latest`의 가격 상태와 활동반경 필드를 정식 계약으로 포함한다.

## 1. 현재 계약 요약
- 브라우저는 Supabase 공개 뷰 3개만 직접 조회한다.
- 읽기용 FastAPI 경로는 rollback-only 레거시 경로다.
- 먹이 탐색 탭은 단일 카드 1장만 사용한다.
- freshness 기준은 `20시간`이다.
- 카드 가격 상태와 활동반경은 `v_stock_detail_latest` 계약에서 완결된다.

## 2. 런타임 계약

### 브라우저 런타임 값
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

### 금지 값
- `SUPABASE_SERVICE_ROLE_KEY`
- `DART_API_KEY`
- 배치/관리용 쓰기 권한 값

## 3. Source of Truth
- `ticker_universe`
  - 종목 마스터
- `market_snapshot_daily`
  - 최신 시세 원본
- `fundamentals_cache`
  - 종목 상세 요약/재무/가격 상태/활동반경 캐시
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
| `ai_summary` | `text` | 요약 문장 |

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
- 검색 결과는 숨기지 않고 카드 상태 명시를 우선한다

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
| `price_status` | `text` | `live`, `fallback`, `missing` |
| `price_source` | `text` | `snapshot`, `cache_fallback`, `unavailable` |
| `safe_activity_radius_pct` | `numeric` | 안전 활동반경 퍼센트 |
| `safe_activity_level` | `text` | `safe`, `caution`, `danger` |
| `safe_activity_label` | `text` | 활동반경 설명 문구 |

동작 규칙:
- 가격 우선순위는 `latest snapshot.close -> cache fallback price -> null`
- 기본 카드 심볼은 `AAPL`
- 검색 선택 후에도 같은 카드 1장을 교체한다
- 브라우저는 추가 라이브 폴백을 하지 않는다
- 카드가 직접 계산하지 않고 계약에서 내려준 활동반경을 그대로 쓴다

프론트 표시 규칙:
- `market = KR`면 `KRW`
- `market = US`면 `USD`
- `price_status = missing`이면 `가격 준비중`
- `price_status = fallback`이면 캐시 보강 가격 안내를 허용
- 활동반경은 `±X.X%`와 단계 배지로 표시한다

## 5. 활동반경 계산 계약
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
- 단계 매핑
  - `>= 4.5%`면 `safe`
  - `>= 3.0%`면 `caution`
  - `< 3.0%`면 `danger`

## 6. 품질 게이트
- freshness `20시간`
- 대표 종목 `AAPL`, `TSLA`, `000660.KS`
- empty summary overwrite 금지
- 카드 빈 가격 상태 허용 금지
- 활동반경 범위 위반 금지
- 브라우저는 공개 뷰 3개만 조회해야 한다

## 7. rollback 계약
- rollback-only 레거시 경로
  - `/api/market-summary`
  - `/api/stocks/search`
  - `/api/stocks/{symbol}`
- 위 경로는 신규 주 경로가 아니다

## 8. 현재 보류 범위
- 트렌딩 UI
- 생존 일지 저장/복원
- 로그인/계정
- 실시간 시세 스트리밍
