from __future__ import annotations

from services import kr_market_ingestion


def test_collect_kr_snapshot_uses_krx_when_key_exists(monkeypatch):
    calls = []
    monkeypatch.setattr(kr_market_ingestion.settings, "KRX_AUTH_KEY", "secret")
    monkeypatch.setattr(kr_market_ingestion, "_collect_krx_snapshot", lambda symbols, target_date=None: calls.append(("krx", list(symbols))) or [{"symbol": "005930.KS", "market": "KR", "snapshot_date": "2026-03-23", "close": 1000, "change_pct": 1.1, "volume": 100, "market_cap": None, "per": None, "pbr": None, "payload": {"price_source": "krx_official"}}])
    monkeypatch.setattr(kr_market_ingestion, "_collect_kr_yfinance_snapshot", lambda symbols, target_date=None: calls.append(("yfinance", list(symbols))) or [])

    rows = kr_market_ingestion.collect_kr_snapshot(["005930.KS"])

    assert rows[0]["payload"]["price_source"] == "krx_official"
    assert calls == [("krx", ["005930.KS"])]


def test_collect_kr_snapshot_falls_back_to_yfinance_when_key_is_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(kr_market_ingestion.settings, "KRX_AUTH_KEY", "")
    monkeypatch.setattr(kr_market_ingestion, "_collect_krx_snapshot", lambda symbols, target_date=None: calls.append(("krx", list(symbols))) or [])
    monkeypatch.setattr(kr_market_ingestion, "_collect_kr_yfinance_snapshot", lambda symbols, target_date=None: calls.append(("yfinance", list(symbols))) or [{"symbol": "000660.KS", "market": "KR", "snapshot_date": "2026-03-23", "close": 1000, "change_pct": 0.5, "volume": 100, "market_cap": None, "per": None, "pbr": None, "payload": {"price_source": "yfinance_fallback"}}])

    rows = kr_market_ingestion.collect_kr_snapshot(["000660.KS"])

    assert rows[0]["payload"]["price_source"] == "yfinance_fallback"
    assert calls == [("yfinance", ["000660.KS"])]
