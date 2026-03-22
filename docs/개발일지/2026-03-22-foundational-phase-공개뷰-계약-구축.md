# foundational phase 공개뷰 계약 구축

## 작성시각
2026-03-22 12:09:24 KST

## 해결하고자 한 문제
Setup만 끝낸 상태로는 실제 Supabase 직결 구현을 시작할 수 없었다. 공개 뷰 SQL, RLS/권한 계약, 브라우저 query/helper, adapter, 그리고 그 계약을 검증하는 테스트가 먼저 있어야 다음 story 구현이 흔들리지 않는다.

## 이번 단계에서 한 일
- `supabase/migrations/20260322_public_market_views.sql`를 추가해 공개 뷰 3개와 기본 grant/RLS 잠금 방향을 넣었다.
- `src/lib/supabase-adapters.js`, `src/lib/supabase-queries.js`를 추가해 snake_case -> UI adapter와 direct-read query helper를 만들었다.
- `backend/tests/test_public_views_contract.py`, `src/tests/supabase-direct-mapping.test.ts`, `src/tests/supabase-direct-query.test.ts`를 추가했다.
- `pnpm lint`, `pnpm typecheck`, `pnpm test`, `python -m pytest backend/tests/test_public_views_contract.py`를 실행해 현재 추가 범위를 검증했다.
- `docs/task.md`에서 T006~T011를 완료 처리했다.

## 해결된 것
- 공개 뷰 계약과 브라우저 direct-read helper의 최소 기반이 생겼다.
- 현재 Foundational 범위는 문서뿐 아니라 테스트 기준으로도 검증 가능해졌다.
- Setup + Foundational이 모두 체크오프 가능한 상태가 됐다.

## 해결되지 않은 것
- `index.html`은 아직 FastAPI `/api/...`를 호출한다.
- `US1`과 이후 story는 아직 구현 전이다.
- migration SQL은 아직 실제 Supabase에 적용하지 않았다.

## 메모
이번 단계부터는 실제 직결 구현 기반이 들어갔고, 다음 단계는 오늘 탭/기본 카드 전환이 중심이 된다.
