# Supabase Direct-Read Spec

## 작성시각
2026-03-22 12:34:06 KST

## 공개 뷰 계약
- `v_home_summary`
  - 오늘 탭 단일 행 공급
- `v_stock_search`
  - 검색 리스트 공급
- `v_stock_detail_latest`
  - 카드용 최신 종목 상세 공급

## 프론트 계약
- 브라우저 런타임 값
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
- snake_case SQL 결과는 adapter에서 UI shape로 변환
- KR 통화는 `KRW`, US 통화는 `USD`

## 품질 게이트
- freshness `20시간`
- 대표 종목 `AAPL`, `TSLA`, `000660.KS`
- empty summary overwrite 금지
- 검색 정렬 우선순위
  1. symbol exact
  2. symbol prefix
  3. name prefix
  4. contains

## 롤백 계약
- `/api/market-summary`
- `/api/stocks/search`
- `/api/stocks/{symbol}`

위 세 경로는 신규 주 경로가 아니라 rollback-only 레거시 경로다.
