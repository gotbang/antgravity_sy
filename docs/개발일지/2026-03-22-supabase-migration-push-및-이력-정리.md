# Supabase migration push 및 이력 정리

## 작성시각
2026-03-22 20:43:24 KST

## 해결하고자 한 문제
로컬 코드와 migration 파일은 이미 준비됐는데 `supabase db push`가 `up to date`로 나오거나, 이후에는 remote migration history 불일치 때문에 push가 막히는 상태였다. 실제 원격 DB에 새 스키마를 반영하고, 최소한 한 번은 정상 적용되게 만드는 게 목표였다.

## 이번 단계에서 한 일
- 새 migration 파일 `supabase/migrations/20260322110000_ingestion_coverage_v2.sql`을 추가했다.
- `npx.cmd supabase migration repair --status reverted 20260322`로 원격 이력을 한 번 복구한 뒤 다시 `npx.cmd supabase db push`를 실행했다.
- push 실패 원인이던 `refresh_bucket` 누락과 view 교체 충돌을 migration 파일에서 수정했다.
- 최종적으로 새 migration 파일과 `20260322_public_market_views.sql`이 원격에 적용되는 것까지 확인했다.
- 이후 반복 `db push`에서 legacy `20260322` 이력 불일치가 다시 보이는 문제를 줄이기 위해 기존 `20260321`, `20260322` 파일은 원상복구하고, 실제 변경점은 새 migration 파일 하나로 정리했다.

## 해결된 것
- 원격 DB에 `symbol_ingestion_state`, `symbol_ingestion_failure_log`, `symbol_refresh_requests`, coverage/stale view 변경이 한 번 적용됐다.
- 새 migration 파일만 실제 변경점이 되도록 로컬 migration 구성을 정리했다.
- public view 계약 테스트는 새 migration 파일 기준으로 다시 통과했다.

## 해결되지 않은 것
- `supabase migration list` 출력은 legacy 8자리 migration(`20260322`) 때문에 계속 매칭이 어색하게 보인다.
- 그래서 추후 반복 `db push`에서는 여전히 `migration repair` 또는 `db pull` 기반 정리가 한 번 더 필요할 수 있다.
- exact worker 외부 크론 자체는 아직 연결하지 않았다.

## 메모
- 이번 단계의 핵심은 “원격 적용”이었고, 그 목적은 달성했다.
- 다만 migration history 자체는 깔끔하지 않아서, 다음 운영 단계에선 `db pull`로 로컬 이력을 다시 정리하는 걸 권장한다.
