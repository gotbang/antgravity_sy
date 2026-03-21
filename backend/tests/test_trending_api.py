from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_trending_endpoint_exists():
    response = client.get('/api/market/trending')
    assert response.status_code in {200, 503}
