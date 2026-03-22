from __future__ import annotations

import pandas as pd

from services import kr_market_ingestion


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
