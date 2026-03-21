from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_stock_search_endpoint_exists():
    response = client.get('/api/stocks/search', params={'q': '삼성'})
    assert response.status_code == 200
