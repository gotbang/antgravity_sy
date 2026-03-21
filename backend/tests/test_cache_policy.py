from services.cache_policy import should_live_fetch


def test_should_live_fetch_price_only():
    assert should_live_fetch('price') is True
    assert should_live_fetch('fundamentals') is False
    assert should_live_fetch('summary') is False
