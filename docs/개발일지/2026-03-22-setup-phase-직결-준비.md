# setup phase 직결 준비

## 작성시각
2026-03-22 11:52:05 KST

## 해결하고자 한 문제
`docs/task.md` 기준 구현을 시작하려면 먼저 프론트 검증 환경과 브라우저 Supabase 진입점이 있어야 했는데, 현재 저장소에는 `package.json`, `tsconfig.json`, `vitest.config.ts`, 공개 env 템플릿, 브라우저 Supabase 클라이언트가 모두 없었다.

## 이번 단계에서 한 일
- 루트 `package.json`을 추가해 `pnpm lint`, `pnpm typecheck`, `pnpm test` 스크립트를 만들었다.
- `tsconfig.json`, `vitest.config.ts`, `eslint.config.js`를 추가해 프론트 검증 기반을 만들었다.
- `src/config/public-env.js`, `src/lib/supabase-browser.js`를 추가해 공개 env와 브라우저 Supabase 클라이언트 진입점을 만들었다.
- `.gitignore`에 `.pnpm-store/`를 추가했다.
- `docs/quickstart.md`를 현재 setup 상태에 맞게 갱신했고, `docs/task.md`에서 T001~T005, T012를 완료 처리했다.

## 해결된 것
- Setup phase의 핵심 준비 태스크를 실제 파일로 반영했다.
- 프론트 검증 명령과 브라우저 Supabase 진입점이 문서와 저장소 양쪽에 생겼다.

## 해결되지 않은 것
- 의존성 설치는 아직 하지 않았다.
- 공개 뷰, RLS, adapter, query layer 같은 Foundational phase는 아직 시작 전이다.
- 실제 lint/typecheck/test 실행 결과는 아직 확인하지 않았다.

## 메모
이번 단계는 Setup 중심 구현이었고, 아직 Supabase 직결 동작 자체는 붙이지 않았다.
