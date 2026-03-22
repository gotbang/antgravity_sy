# Supabase migration push 및 이력 정리 프롬프트

## 작성시각
2026-03-22 20:43:24 KST

## 프롬프트 내용
```text
새 migration 파일 내용으로 정리해서 직접 db push해줘
```

## 이번 단계 해석
- 새 migration 파일을 만들어 기존 변경을 재적용 가능한 형태로 정리해야 했다.
- 그다음 실제 원격 Supabase DB에 `db push`를 직접 실행해야 했다.
- push 중 migration history 충돌이 생기면 repair까지 포함해서 실제 반영이 되도록 끝까지 처리해야 했다.

## 결과
- `20260322110000_ingestion_coverage_v2.sql`을 추가했다.
- 원격 DB에 새 migration과 view 변경을 한 번 적용했다.
- legacy `20260322` migration 이력 충돌은 남아 있어서, 추후 반복 push 전에 `db pull` 또는 추가 history 정리가 필요하다는 점도 기록했다.
