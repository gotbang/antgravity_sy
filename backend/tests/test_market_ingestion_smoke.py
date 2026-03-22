from __future__ import annotations

import pandas as pd

from services import kr_market_ingestion
from services import us_market_ingestion


def test_kr_market_snapshot_includes_ohlcv_only_tickers(monkeypatch):
    fundamental_frame = pd.DataFrame(
        {'PER': [10.5], 'PBR': [1.2]},
        index=['005930']
    )
    ohlcv_frame = pd.DataFrame(
        {'종가': [100000, 210000], '등락률': [1.1, 2.2], '거래량': [10, 20]},
        index=['005930', '000660']
    )

    monkeypatch.setattr(kr_market_ingestion, '_resolve_kr_business_day', lambda _date=None: '20260321')
    monkeypatch.setattr(kr_market_ingestion.stock, 'get_market_fundamental_by_ticker', lambda _date: fundamental_frame)
    monkeypatch.setattr(kr_market_ingestion.stock, 'get_market_ohlcv_by_ticker', lambda _date: ohlcv_frame)

    rows = kr_market_ingestion.collect_kr_market_snapshot()
    symbols = {row['symbol'] for row in rows}

    assert '005930.KS' in symbols
    assert '000660.KS' in symbols


def test_kr_market_snapshot_falls_back_to_yahoo_when_business_day_resolution_fails(monkeypatch):
    monkeypatch.setattr(kr_market_ingestion, '_resolve_kr_business_day', lambda _date=None: None)
    monkeypatch.setattr(
        kr_market_ingestion,
        '_collect_kr_yahoo_fallback_snapshot',
        lambda: [{'symbol': '000660.KS', 'close': 150000, 'market': 'KR'}]
    )

    rows = kr_market_ingestion.collect_kr_market_snapshot()

    assert rows == [{'symbol': '000660.KS', 'close': 150000, 'market': 'KR'}]


def test_us_market_snapshot_falls_back_to_yahoo_chart_for_representative_symbols(monkeypatch):
    monkeypatch.setattr(us_market_ingestion.yf, 'download', lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError('boom')))
    monkeypatch.setattr(
        us_market_ingestion,
        '_fetch_yahoo_chart_snapshot',
        lambda symbol: {
            'symbol': symbol,
            'market': 'US',
            'snapshot_date': '2026-03-21',
            'close': 123.4,
            'change_pct': 1.2,
            'market_cap': None,
            'volume': 1000,
            'per': None,
            'pbr': None,
            'payload': {'price_source': 'yahoo_chart_api'},
        },
    )

    rows = us_market_ingestion.collect_us_snapshot(['AAPL', 'TSLA'])

    assert {row['symbol'] for row in rows} == {'AAPL', 'TSLA'}
    assert all(row['payload']['price_source'] == 'yahoo_chart_api' for row in rows)
