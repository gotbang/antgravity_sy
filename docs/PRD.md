# AntGravity Supabase Direct-Read PRD

## 작성시각
2026-03-22 12:34:06 KST

## 제품 목표
AntGravity 주식 모드의 읽기 경로를 `정적 프론트 + Supabase direct-read` 구조로 전환해 FastAPI 읽기 의존을 줄이고, 공개 뷰 3개를 기반으로 오늘 탭, 검색 결과, 종목 상세 카드 경험을 안정화한다.

## 핵심 사용자 가치
- 오늘 탭을 더 단순한 읽기 구조로 빠르게 본다.
- 검색 결과를 리스트로 확인하고 원하는 종목을 고를 수 있다.
- 기본 카드와 선택 종목 카드가 같은 direct-read 계약으로 일관되게 갱신된다.

## 범위
- 포함
  - `v_home_summary`
  - `v_stock_search`
  - `v_stock_detail_latest`
  - 오늘 탭
  - 검색 결과 리스트
  - 기본 카드/선택 카드
- 제외
  - 트렌딩 UI
  - 생존 일지 저장
  - 로그인/계정
  - 실시간 시세 스트리밍

## 품질 기준
- 대표 KR 종목 `000660.KS`
- 대표 US 종목 `AAPL`, `TSLA`
- freshness 기준 `20시간`
- 브라우저 라이브 폴백 없음
- rollback-only FastAPI 읽기 경로 유지
