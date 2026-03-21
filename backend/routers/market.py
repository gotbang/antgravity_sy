from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.market_query_service import load_market_summary, load_trending

router = APIRouter()


@router.get('/market-summary')
def get_market_summary() -> dict:
    try:
        return load_market_summary()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get('/market/trending')
def get_trending() -> dict:
    try:
        return load_trending()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
