from scripts.daily_refresh import REQUIRED_QUALITY_GATE_SYMBOLS, _has_required_quality_gate_rows


def test_required_quality_gate_symbols_match_plan_contract():
    assert REQUIRED_QUALITY_GATE_SYMBOLS == ('AAPL', 'TSLA', '000660.KS')


def test_quality_gate_requires_all_representative_symbols():
    rows = [
        {'symbol': 'AAPL', 'close': 100},
        {'symbol': 'TSLA', 'close': 200},
    ]
    assert _has_required_quality_gate_rows(rows) is False


def test_quality_gate_passes_when_all_representative_symbols_exist():
    rows = [
        {'symbol': 'AAPL', 'close': 100},
        {'symbol': 'TSLA', 'close': 200},
        {'symbol': '000660.KS', 'close': 300},
    ]
    assert _has_required_quality_gate_rows(rows) is True


def test_quality_gate_fails_when_representative_symbol_price_is_missing():
    rows = [
        {'symbol': 'AAPL', 'close': 100},
        {'symbol': 'TSLA', 'close': None},
        {'symbol': '000660.KS', 'close': 300},
    ]
    assert _has_required_quality_gate_rows(rows) is False
