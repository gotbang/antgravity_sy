# kr snapshot 적재 원인 디버깅 프롬프트

## 작성시각
2026-03-22 12:37:23 KST

## 프롬프트 내용
```text
000660.KS가 왜 price = null인지
적재 문제인지 뷰 조인 문제인지
바로 디버깅해줘. 그런데 개발일지랑 프롬프트일지 참고해. 거기에 비슷한 문제점이 적혀있는거로 안다

개발일지랑 프롬프트 폴더안의 문서 먼저확인후 문제해결. Pykrx가 호출이 안되서 yfinance를 썼었다
```

## 이번 단계 해석
- 먼저 과거 개발일지/프롬프트에서 `PyKRX`와 `Yahoo fallback` 문맥을 다시 읽고 시작해야 했다.
- `000660.KS` null 가격의 원인을 적재와 뷰 조인 중 하나로 좁혀야 했다.
- 원인만 찾는 게 아니라 실제 적재 경로 수정과 재적재 확인까지 가야 했다.

## 결과
- `ticker_universe`에는 row가 있지만 `market_snapshot_daily`가 비어 있어서 뷰가 `price = null`을 만들고 있음을 확인했다.
- `PyKRX` business-day helper 실패가 근본 원인임을 확인했다.
- Yahoo chart fallback snapshot 경로를 KR 적재에 넣고 배치를 다시 돌려 `000660.KS` snapshot row를 채웠다.
