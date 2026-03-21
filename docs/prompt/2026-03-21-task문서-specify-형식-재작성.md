# task문서 specify 형식 재작성 프롬프트

## 작성시각
2026-03-21 19:50:52 KST

## 프롬프트 내용
```text
PLEASE IMPLEMENT THIS PLAN:
# `docs/task.md` 재작성 계획

## Summary
- 새 task 문서는 기존 docs/task.md를 전면 교체해서 `Specify 체크리스트 형식`으로 다시 쓴다.
- task 생성 기준은 docs/plan.md 전체가 아니라, 최신 우선 원칙에 따라 `7. 실데이터 연동 계획`을 메인으로 삼는다.
- 사용자 스토리는 3개로 고정한다.
```

## 이번 단계 해석
- `.specify`와 `spec.md`는 저장소에 없어서 수동 합성 방식으로 task를 작성
- `docs/plan.md` 7장 기준으로 사용자 스토리 구성
- 기존 자유형 `docs/task.md`는 전면 교체
- 문서만 수정하고 소스코드는 변경하지 않음

## 결과
- `docs/task.md` 전면 재작성
- 이번 단계 기록 문서 추가
