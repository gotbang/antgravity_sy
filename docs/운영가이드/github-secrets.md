# GitHub Secrets Guide

## Required Secrets
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: service_role key for batch upsert and API server reads
- `DART_API_KEY`: OpenDART/Dartlab API key

## Workflow Policy
- 배치는 `미국장 마감 후 하루 1회` 실행한다.
- 원본 진실 소스는 Supabase다.
- 파일 캐시는 비추적 산출물이며 git에 커밋하지 않는다.
- 실패 시 `workflow_dispatch`로 특정 단계 재실행이 가능해야 한다.
