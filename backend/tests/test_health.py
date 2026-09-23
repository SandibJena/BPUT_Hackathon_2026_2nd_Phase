from app.core.config import settings

def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "disclaimer" in data
    assert data["disclaimer"] == settings.DISCLAIMER
