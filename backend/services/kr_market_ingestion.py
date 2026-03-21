from __future__ import annotations

from typing import Any

from pykrx import stock


def collect_kr_market_snapshot(target_date: str | None = None) -> list[dict[str, Any]]:
    date_str = target_date or stock.get_nearest_business_day_in_a_week()
    frame = stock.get_market_fundamental_by_ticker(date_str)
    ohlcv = stock.get_market_ohlcv_by_ticker(date_str)

    rows: list[dict[str, Any]] = []
    for ticker, item in frame.iterrows():
        price_row = ohlcv.loc[ticker] if ticker in ohlcv.index else None
        rows.append(
            {
                "symbol": f"{ticker}.KS",
                "market": "KR",
                "snapshot_date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
                "close": None if price_row is None else float(price_row.get("종가", 0) or 0),
                "change_pct": None if price_row is None else float(price_row.get("등락률", 0) or 0),
                "market_cap": None,
                "volume": None if price_row is None else int(price_row.get("거래량", 0) or 0),
                "per": float(item.get("PER", 0) or 0) or None,
                "pbr": float(item.get("PBR", 0) or 0) or None,
                "payload": {
                    "price_source": "PyKRX",
                },
            }
        )
    return rows


def collect_kr_universe() -> list[dict[str, Any]]:
    tickers = stock.get_market_ticker_list(market="ALL")
    rows: list[dict[str, Any]] = []
    for ticker in tickers:
        name = stock.get_market_ticker_name(ticker)
        rows.append(
            {
                "symbol": f"{ticker}.KS",
                "market": "KR",
                "name": name,
                "sector": None,
                "industry": None,
            }
        )
    return rows
