# GitHub Secrets Guide

## 작성시각
2026-03-22 11:21:58 KST

## 문서 목적
이 문서는 현재 구현 기준 시크릿 사용 범위와, 다음 구현 예정으로 남겨둔 시크릿 분리 계획을 함께 정리한다.

## 1. 현재 구현 기준 시크릿

### 백엔드/배치에서 사용하는 값
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DART_API_KEY`

### 현재 용도
- FastAPI 서버가 Supabase 데이터를 읽을 때 사용한다.
- GitHub Actions 배치가 유니버스, snapshot, cache를 적재할 때 사용한다.
- 브라우저에는 현재 이 값들을 넣지 않는다.

## 2. 현재 브라우저 문맥

- 현재 프론트는 `/api/...` 경로만 호출한다.
- 즉, 현재 구현 기준으로 브라우저에 필요한 Supabase 키는 없다.
- 따라서 현재 상태에서 `SUPABASE_SERVICE_ROLE_KEY`는 물론이고 `SUPABASE_ANON_KEY`도 프론트 필수값이 아니다.

### 직결 전환 이후 브라우저 문맥
- direct-read 전환이 완료되면 브라우저 런타임에는 `SUPABASE_URL`, `SUPABASE_ANON_KEY`만 둔다.
- `SUPABASE_SERVICE_ROLE_KEY`, `DART_API_KEY`는 여전히 브라우저 금지 값이다.
- legacy FastAPI 읽기 경로는 rollback-only 문맥으로만 남긴다.

## 3. 절대 브라우저에 넣으면 안 되는 값

- `SUPABASE_SERVICE_ROLE_KEY`
- `DART_API_KEY`
- 배치용 쓰기 권한 키
- 마이그레이션/관리용 시크릿

## 4. GitHub Actions 현재 사용값

- 워크플로 파일: `.github/workflows/daily-market-refresh.yml`
- 현재 주입되는 환경값
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DART_API_KEY`
- 설치 명령
  - `python -m pip install --upgrade pip`
  - `pip install -r backend/requirements.txt`
- 실행 명령
  - `python backend/scripts/daily_refresh.py --phase ${{ github.event.inputs.phase || 'all' }}`

## 5. 다음 구현 예정으로 남겨둘 분리 계획

### 후속 아키텍처가 승인될 때의 후보
- 프론트 런타임 후보
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
- 비브라우저 문맥 유지값
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DART_API_KEY`

### 메모
- 이 항목은 현재 사용 중인 구조가 아니라 후속 검토 계획이다.
- `SUPABASE_ANON_KEY`가 문서에 남아 있는 이유는 삭제하지 말라는 요청에 따라 미래 계획을 별도 보존하기 위해서다.

## 6. 확인 체크리스트

- 현재 구현 기준과 후속 계획을 같은 문장으로 섞지 않았는가
- 브라우저 문맥에 `SUPABASE_SERVICE_ROLE_KEY`를 넣지 않았는가
- 현재 워크플로와 후속 후보 시크릿을 분리해 적었는가
