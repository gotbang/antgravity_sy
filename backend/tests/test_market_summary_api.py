from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_market_summary_endpoint_exists():
    response = client.get('/api/market-summary')
    assert response.status_code in {200, 503}
