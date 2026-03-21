from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.market_query_service import load_stock_detail, load_stock_search

router = APIRouter()


@router.get('/stocks/search')
def search_stocks(q: str = Query(..., min_length=1)) -> dict:
    return load_stock_search(q)


@router.get('/stocks/{symbol}')
def get_stock(symbol: str) -> dict:
    try:
        return load_stock_detail(symbol)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
