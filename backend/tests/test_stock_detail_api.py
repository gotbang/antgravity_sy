from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_stock_detail_endpoint_exists():
    response = client.get('/api/stocks/005930.KS')
    assert response.status_code in {200, 503}
