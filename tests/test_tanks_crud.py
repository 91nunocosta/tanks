from fastapi.testclient import TestClient

from tanks.models import Thank


def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 404

    assert Thank()
