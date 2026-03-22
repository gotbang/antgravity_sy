from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routers.market import router as market_router
from routers.stocks import router as stocks_router

app = FastAPI(title='AntGravity Market API', version='0.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(market_router, prefix='/api')
app.include_router(stocks_router, prefix='/api')


@app.get('/api/health')
def health() -> dict:
    return {'status': 'ok'}
