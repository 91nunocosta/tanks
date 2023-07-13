from datetime import datetime
from typing import Any, Generator

import dateutil.parser
from fastapi.testclient import TestClient
from pytest import fixture
from sqlmodel import Session

from tanks.models import Tank, TankVolume


@fixture(name="tank_volumes")
def tank_volumes_fixture(session: Session) -> Generator:
    session.add(Tank(id=1, name="ULS Diesel"))
    session.add(Tank(id=2, name="Top Diesel"))

    session.add(
        TankVolume(id=4, tank_id=2, volume=10, created_at=datetime(2023, 1, 15, 14, 0))
    )

    tank_volumes = [
        TankVolume(id=1, tank_id=1, volume=10, created_at=datetime(2023, 1, 1, 10, 0)),
        TankVolume(id=2, tank_id=1, volume=45, created_at=datetime(2023, 1, 8, 9, 0)),
        TankVolume(id=3, tank_id=1, volume=10, created_at=datetime(2023, 1, 15, 14, 0)),
    ]

    for tank_volume in tank_volumes:
        session.add(tank_volume)

    session.commit()

    yield tank_volumes


def as_dict(tank_volume: TankVolume) -> dict[str, Any]:
    result = tank_volume.dict()
    result["created_at"] = tank_volume.created_at.isoformat()
    return result


def test_create(session: Session, client: TestClient):
    session.add(Tank(id=1, name="USL Diesel"))
    response = client.post(
        "/tanks/1/volumes",
        json={
            "volume": 10.0,
        },
    )

    assert response.status_code == 201

    created_tank_volume = response.json()
    assert created_tank_volume

    created_tank_volume_id = created_tank_volume.get("id")
    assert created_tank_volume_id is not None

    assert created_tank_volume.get("tank_id") == 1
    assert created_tank_volume.get("volume") == 10
    created_at = created_tank_volume.get("created_at")
    assert created_at
    created_at_datetime = dateutil.parser.isoparse(created_at)
    assert (datetime.now() - created_at_datetime).total_seconds() < 1
    assert session.query(TankVolume).filter_by(id=created_tank_volume_id).first()


def test_get_one(client: TestClient, tank_volumes: list[TankVolume]):
    tank_volume = tank_volumes[0]

    response = client.get(f"/tanks/{tank_volume.tank_id}/volumes/{tank_volume.id}")

    assert response.status_code == 200
    assert response.json() == as_dict(tank_volume)


def test_get_one_miss(client: TestClient, tank_volumes: list[TankVolume]):
    response = client.get(f"/tanks/{tank_volumes[0].tank_id}/volumes/1000")
    assert response.status_code == 404

    response = client.get(f"/tanks/1000/volumes/{tank_volumes[0].id}")
    assert response.status_code == 404


def test_get_many(client: TestClient, tank_volumes: list[TankVolume]):
    response = client.get(f"/tanks/{tank_volumes[0].tank_id}/volumes?offset=0&limit=10")

    assert response.status_code == 200
    assert response.json().get("items") == [
        as_dict(tank_volume) for tank_volume in tank_volumes
    ]
    assert response.json().get("total") == len(tank_volumes)
    assert response.json().get("limit") == 10
    assert response.json().get("offset") == 0


def test_many_offset(client: TestClient, tank_volumes: list[TankVolume]):
    response = client.get("/tanks/1/volumes?offset=1&limit=10")

    assert response.status_code == 200
    assert response.json().get("items") == [
        as_dict(tank_volume) for tank_volume in tank_volumes[1:]
    ]
    assert response.json().get("offset") == 1


def test_many_limit(client: TestClient, tank_volumes: list[TankVolume]):
    response = client.get("/tanks/1/volumes?offset=0&limit=2")

    assert response.status_code == 200
    assert response.json().get("items") == [
        as_dict(tank_volume) for tank_volume in tank_volumes[:2]
    ]
    assert response.json().get("limit") == 2


def test_update(session: Session, client: TestClient, tank_volumes: list[TankVolume]):
    tank_volume = tank_volumes[0]
    tank_volume.volume += 10

    response = client.patch(
        f"/tanks/1/volumes/{tank_volume.id}",
        json={
            "volume": tank_volume.volume,
        },
    )

    assert response.status_code == 200
    assert response.json() == as_dict(tank_volumes[0])
    updated_tank = session.query(TankVolume).filter_by(id=tank_volume.id).first()
    assert updated_tank
    assert updated_tank.volume == tank_volume.volume


def test_update_miss(
    client: TestClient, tank_volumes: list[TankVolume]
):  # pylint: disable=unused-argument
    response = client.patch(
        "/tanks/1/volumes/1000",
        json={"volume": 10},
    )
    assert response.status_code == 404

    response = client.patch(
        "/tanks/1000/volumes/1",
        json={"volume": 10},
    )
    assert response.status_code == 404


def test_delete(session: Session, client: TestClient, tank_volumes: list[TankVolume]):
    tank_volume = tank_volumes[0]

    response = client.delete(f"/tanks/{tank_volume.tank_id}/volumes/{tank_volume.id}")

    assert response.status_code == 204
    assert session.query(TankVolume).filter_by(id=tank_volume.id).count() == 0


def test_delete_miss(
    client: TestClient, tank_volumes: list[TankVolume]
):  # pylint: disable=unused-argument
    response = client.delete("/tanks/1/volumes/1000")
    assert response.status_code == 404

    response = client.delete("/tanks/1000/volumes/1")
    assert response.status_code == 404
