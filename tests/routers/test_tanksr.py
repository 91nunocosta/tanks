from typing import Generator

from fastapi.testclient import TestClient
from pytest import fixture
from sqlmodel import Session

from tanks.models import Tank


@fixture(name="tanks")
def tanks_fixture(session: Session) -> Generator:
    tanks = [
        Tank(id=1, name="ULS Diesel"),
        Tank(id=2, name="93 Premium Gasoline"),
        Tank(id=3, name="Top Diesel"),
    ]

    for tank in tanks:
        session.add(tank)
    session.commit()

    yield tanks


def test_create(session: Session, client: TestClient):
    tank_name = "ULS Diesel"

    response = client.post(
        "/tanks",
        json={
            "name": tank_name,
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == tank_name

    assert session.query(Tank).filter_by(id=response.json()["id"]).first()


def test_get_one(session: Session, client: TestClient, tanks: list[Tank]):
    tank = tanks[0]
    session.add(tank)
    session.commit()

    response = client.get(f"/tanks/{tank.id}")

    assert response.status_code == 200
    assert response.json() == tank.dict()


def test_get_one_miss(client: TestClient):
    response = client.get("/tanks/1")

    assert response.status_code == 404


def test_many(client: TestClient, tanks: list[Tank]):
    response = client.get("/tanks?offset=0&limit=10")

    assert response.status_code == 200
    assert response.json().get("items") == [tank.dict() for tank in tanks]
    assert response.json().get("total") == len(tanks)
    assert response.json().get("limit") == 10
    assert response.json().get("offset") == 0


def test_many_offset(client: TestClient, tanks: list[Tank]):
    response = client.get("/tanks?offset=1&limit=10")

    assert response.status_code == 200
    assert response.json().get("items") == [tank.dict() for tank in tanks[1:]]
    assert response.json().get("offset") == 1


def test_many_limit(client: TestClient, tanks: list[Tank]):
    response = client.get("/tanks?offset=0&limit=2")

    assert response.status_code == 200
    assert response.json().get("items") == [tank.dict() for tank in tanks[:2]]
    assert response.json().get("limit") == 2


def test_update(session: Session, client: TestClient, tanks: list[Tank]):
    tank_id = tanks[0].id
    new_name = tanks[0].name + " Top"

    response = client.put(
        f"/tanks/{tank_id}",
        json={
            "name": new_name,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"id": tank_id, "name": new_name}
    updated_tank = session.query(Tank).filter_by(id=tank_id).first()
    assert updated_tank
    assert updated_tank.name == new_name


def test_update_miss(client: TestClient):
    response = client.put(
        "/tanks/1",
        json={
            "name": "ULS Diesel",
        },
    )

    assert response.status_code == 404


def test_delete(session: Session, client: TestClient, tanks: list[Tank]):
    tank = tanks[0]

    response = client.delete(f"/tanks/{tank.id}")

    assert response.status_code == 204
    assert session.query(Tank).filter_by(id=tank.id).count() == 0


def test_delete_miss(client: TestClient):
    response = client.delete("/tanks/1")

    assert response.status_code == 404
