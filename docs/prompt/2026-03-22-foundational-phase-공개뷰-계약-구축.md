# foundational phase 공개뷰 계약 구축 프롬프트

## 작성시각
2026-03-22 12:09:24 KST

## 프롬프트 내용
```text
docs/task.md를 100% 이해후 아주 디테일하게 구현.
```

## 이번 단계 해석
- Setup phase 다음으로 바로 Foundational phase를 실제 코드와 테스트로 반영해야 했다.
- 공개 뷰, RLS 방향, direct-read helper, adapter, 계약 테스트가 다음 story의 선행조건이라고 판단했다.
- 완료된 태스크는 `docs/task.md`에 즉시 `[X]`로 반영해야 했다.

## 결과
- 공개 뷰 migration, browser query/helper, adapter, 계약 테스트를 추가했다.
- lint/typecheck/test/pytest 검증까지 통과시켰다.
- `docs/task.md`에서 Foundational 범위 태스크를 완료 처리했다.
