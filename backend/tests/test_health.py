from fastapi.testclient import TestClient

from app.core.config import DISCLAIMER, Settings
from app.main import create_app


def test_health_and_processing_disabled(tmp_path):
    settings = Settings(_env_file=None, app_env='test', database_url=f"sqlite:///{tmp_path / 'api.db'}")
    with TestClient(create_app(settings)) as client:
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json()['processing_enabled'] is False
        assert response.json()['synthetic_only'] is True
        assert response.json()['disclaimer'] == DISCLAIMER
        assert client.post('/intake/text', json={'text': 'synthetic'}).status_code == 404
