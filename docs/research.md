# AntGravity 구현 기준 리서치

## 작성시각
2026-03-22 16:20:06 KST

## 문서 목적
이 문서는 현재 direct-read 구현 상태와 최신 후속 개선 결과를 기준으로 AntGravity 주식 모드의 구조와 리스크를 정리한다. 이번 갱신에서는 먹이 탐색 가격 공백 원인과 해결 방향, 활동반경 실데이터화 결과를 함께 반영한다.

## 1. 현재 구현 기준
- 현재 주식 모드는 `정적 HTML + Supabase direct-read + 배치 적재` 구조로 동작한다.
- 오늘 탭은 `v_home_summary`, 검색은 `v_stock_search`, 카드는 `v_stock_detail_latest`를 읽는다.
- 카드는 이제 가격 숫자만이 아니라 `price_status`, `price_source`, `safe_activity_radius_pct`, `safe_activity_level`, `safe_activity_label`까지 소비한다.

## 2. 이번 개선에서 해결한 문제

### 가격 공백 원인
- 검색 대상은 `ticker_universe` 기준이라 종목이 넓게 잡힌다.
- 반면 카드 가격은 `market_snapshot_daily` 최신 row가 있어야만 채워진다.
- 그래서 유니버스에는 있지만 snapshot이 없는 종목은 카드 가격이 비어 있었다.

### 해결 방향
- 가격 우선순위를 `latest snapshot.close -> cache fallback price -> null`로 고정했다.
- 현재 배치와 이전 snapshot을 병합해 이번 적재가 부분적으로 비어도 직전 가격을 최대한 재사용하게 만들었다.
- 카드는 빈 가격 대신 `가격 준비중` 상태를 노출하게 바꿨다.

### 활동반경 문제
- 먹이 탐색 카드의 `안전 활동반경`은 기존에 고정 `±5%` UI였다.
- 사용자가 실제 시장 리스크와 연결된 값으로 이해하기 어려웠다.

### 해결 방향
- 활동반경을 배치에서 계산된 payload와 공개 뷰 계약으로 내리게 바꿨다.
- 계산 기준은 시장 리스크, 종목 변동성, 유동성 리스크다.
- UI는 `±X.X%`, `안전/주의/고위험`, 짧은 설명 문구로 단순화했다.

## 3. 현재 계약 상태

### `v_home_summary`
- 오늘 탭 단일 행 공급
- 리스크 점수와 AI 요약을 direct-read 한다
- 로드 실패 시 가짜 숫자를 유지하지 않는다

### `v_stock_detail_latest`
- 카드 완결 계약
- 가격 상태
  - `live`
  - `fallback`
  - `missing`
- 활동반경
  - `safe_activity_radius_pct`
  - `safe_activity_level`
  - `safe_activity_label`

## 4. 남은 리스크
- US 적재는 여전히 `yfinance`의 `unable to open database file` 이슈가 남아 있다.
- KR 적재는 `PyKRX` 안정성이 장기 리스크다.
- 이번 개선은 가격 공백을 줄이고 UX를 정상화했지만, 전종목 가격 보장을 의미하지는 않는다.

## 5. 후속 범위
- 검색 결과 단계에 가격 상태 배지가 추가돼 선택 전 기대치를 조정할 수 있게 됐다.
- 대표 US 종목은 Yahoo chart fallback이 들어가 적재 공백 완화 범위가 넓어졌다.
- 다음 초점은 대표 종목을 넘어 일반 US 검색 종목의 적재 커버리지를 얼마나 넓힐지 판단하는 거다.

## 6. 결론
- 이번 단계의 핵심은 “가격이 없다”는 사실을 숨기지 않으면서도 카드가 깨지지 않게 만든 점이다.
- 동시에 `안전 활동반경`을 고정 장식이 아니라 실제 적재 데이터 기반 리스크 가이드로 바꿨다.
- 남은 핵심 과제는 여전히 기능 확장보다 적재 안정성 강화다.
