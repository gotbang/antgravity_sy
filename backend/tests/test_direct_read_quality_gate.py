from scripts.daily_refresh import REQUIRED_QUALITY_GATE_SYMBOLS, _has_required_quality_gate_rows


def test_required_quality_gate_symbols_match_plan_contract():
    assert REQUIRED_QUALITY_GATE_SYMBOLS == ('AAPL', 'TSLA', '000660.KS')


def test_quality_gate_requires_all_representative_symbols():
    rows = [
        {'symbol': 'AAPL'},
        {'symbol': 'TSLA'},
    ]
    assert _has_required_quality_gate_rows(rows) is False


def test_quality_gate_passes_when_all_representative_symbols_exist():
    rows = [
        {'symbol': 'AAPL'},
        {'symbol': 'TSLA'},
        {'symbol': '000660.KS'},
    ]
    assert _has_required_quality_gate_rows(rows) is True
