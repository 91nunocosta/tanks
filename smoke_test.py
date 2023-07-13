import httpx
from pytest import fixture


@fixture(name="base_url")
def base_url_fixture():
    return "http://0.0.0.0:8000"


def test_smoke(base_url: str):
    response = httpx.post(f"{base_url}/tanks/", json={"name": "USL Diesel"})
    assert response.status_code == 201

    tank_id = response.json()["id"]

    response = httpx.get(f"{base_url}/tanks/{tank_id}")
    assert response.status_code == 200

    response = httpx.delete(f"{base_url}/tanks/{tank_id}")
    assert response.status_code == 204
