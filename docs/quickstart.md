# Quickstart

## Backend smoke checks
- `python -m py_compile backend/main.py`
- `python -m pytest backend/tests/test_cache_policy.py`
- `python -m pytest backend/tests/test_market_summary_api.py`
- `python -m pytest backend/tests/test_stock_search_api.py`

## Frontend smoke checks
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`

## Notes
- 현재 저장소에는 package.json이 없어 프론트 명령은 후속 세팅 단계에서 실제 연결이 필요하다.
- Python 의존성은 먼저 `pip install -r backend/requirements.txt`가 필요하다.
