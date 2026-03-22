# kr snapshot 적재 원인 디버깅

## 작성시각
2026-03-22 12:37:23 KST

## 해결하고자 한 문제
`000660.KS`가 `v_stock_detail_latest`에서 `price = null`로 내려와 실제 검색 선택 후 카드에 가격이 `-`로 보였다. 이게 뷰 조인 문제인지, 적재 문제인지, 과거 개발일지에 적힌 `PyKRX 호출 실패 -> Yahoo fallback` 문맥과 연결되는지 확인해야 했다.

## 이번 단계에서 한 일
- 개발일지/프롬프트 문서에서 `KR snapshot 안정성`, `PyKRX 호출 실패`, `Yahoo fallback` 관련 기록을 먼저 다시 읽었다.
- service role로 `ticker_universe`, `market_snapshot_daily`, `fundamentals_cache`, `v_stock_detail_latest`를 직접 조회해 `000660.KS` 상태를 확인했다.
- 그 결과 `ticker_universe`에는 row가 있었지만 `market_snapshot_daily`와 `fundamentals_cache`는 비어 있고, 뷰는 left join 결과로 `price = null`만 내려오고 있음을 확인했다.
- `collect_kr_market_snapshot()`를 로컬에서 직접 실행해 보니 `_resolve_kr_business_day()`가 `None`을 반환하고 있었다.
- 프록시를 정리한 뒤 다시 확인하니 `PyKRX` business day helper가 `IndexError`로 실패하는 게 근본 원인임을 확인했다.
- 그래서 `backend/services/kr_market_ingestion.py`에 Yahoo chart fallback snapshot 경로를 넣고, `backend/scripts/daily_refresh.py`의 프록시 정리를 lower-case 환경변수까지 확장했다.
- 배치를 다시 실행해 `000660.KS`와 `005930.KS` snapshot row가 실제로 Supabase에 들어갔는지 확인했다.

## 해결된 것
- 원인은 뷰 조인이 아니라 KR 적재 누락으로 확정됐다.
- 직접 증거:
  - `ticker_universe`: row 있음
  - `market_snapshot_daily`: row 없음 -> 수정 후 row 생김
  - `v_stock_detail_latest`: `price = null` -> 수정 후 `price = 1007000.0`
- 수정 후 `000660.KS`는 Yahoo chart API 기반 snapshot row를 가지게 됐다.

## 해결되지 않은 것
- 정적 프론트는 여전히 루트 `.env`를 자동으로 브라우저에 주입하지 못한다.
- 그래서 실사용 브라우저 검증을 완전히 자동화하려면 `SUPABASE_ANON_KEY`를 안전하게 브라우저 런타임으로 넘기는 경로가 따로 필요하다.

## 메모
이번 디버깅의 결론은 “`000660.KS price = null`의 근본 원인은 `PyKRX` business-day helper 실패로 KR snapshot 적재가 통째로 비는 것”이다.
