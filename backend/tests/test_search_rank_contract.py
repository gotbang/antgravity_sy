from services.market_query_service import _search_rank


def test_search_rank_prefers_exact_symbol_match():
    exact = _search_rank({'symbol': 'AAPL', 'name': 'Apple Inc.'}, 'AAPL')
    prefix = _search_rank({'symbol': 'AAPLX', 'name': 'Apple Extra'}, 'AAPL')
    assert exact < prefix


def test_search_rank_prefers_symbol_prefix_over_name_prefix():
    symbol_prefix = _search_rank({'symbol': '005930.KS', 'name': '삼성전자'}, '005')
    name_prefix = _search_rank({'symbol': '032830.KS', 'name': '005금융'}, '005')
    assert symbol_prefix < name_prefix


def test_search_rank_prefers_name_prefix_over_contains():
    name_prefix = _search_rank({'symbol': '000660.KS', 'name': '하이닉스'}, '하이')
    contains = _search_rank({'symbol': 'AAPL', 'name': '미국하이테크'}, '하이')
    assert name_prefix < contains
