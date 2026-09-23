def test_login_success(client):
    response = client.post("/api/v1/auth/login", data={"username": "health_worker_1", "password": "demo123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure(client):
    response = client.post("/api/v1/auth/login", data={"username": "health_worker_1", "password": "wrong"})
    assert response.status_code == 401
