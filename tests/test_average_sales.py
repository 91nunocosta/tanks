from collections.abc import Callable
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlmodel import Session

from tanks.models import AverageSale, Tank


def test_create_tank_volume(session: Session, client: TestClient):
    session.add(Tank(id=1, name="USL Diesel"))

    with freeze_time("2023-1-1"):
        response = client.post(
            "/tanks/1/volumes",
            json={"volume": 10.0},
        )
        assert response.status_code == 201
        assert session.query(AverageSale).count() == 0

    with freeze_time("2023-1-3"):
        sale_date = datetime(2023, 1, 3, 10, 0)
        response = client.post(
            "/tanks/1/volumes",
            json={"volume": 20.0},
        )
        assert response.status_code == 201

    assert session.query(AverageSale).count() == 5
    first_row = session.query(AverageSale).order_by(AverageSale.date).first()
    assert first_row
    assert first_row.date == sale_date.date()
    assert first_row.total == 10
    assert first_row.sales == 1
    assert all(row.average == 10 for row in session.query(AverageSale).all())


AddTankVolumeFunction = Callable[[datetime, float], int]


@pytest.fixture(name="add_tank_volume")
def add_tank_volume_fixture(
    session: Session, client: TestClient
) -> AddTankVolumeFunction:
    session.add(Tank(id=1, name="USL Diesel"))

    def _func(created_at: datetime, volume: float) -> int:
        response = client.post(
            "/tanks/1/volumes",
            json={
                "tank_id": 1,
                "volume": volume,
                "created_at": created_at.isoformat(),
            },
        )
        assert response.status_code == 201
        return response.json()["id"]

    return _func


def test_update_tank_volume(
    session: Session, client: TestClient, add_tank_volume: AddTankVolumeFunction
):
    add_tank_volume(datetime(2023, 1, 1, 10, 0), 10)
    id2 = add_tank_volume(datetime(2023, 1, 3, 10, 0), 20)
    assert session.query(AverageSale).count() > 0

    response = client.patch(
        f"/tanks/1/volumes/{id2}",
        json={"volume": 30},
    )
    assert response.status_code == 200
    assert all(row.average == 20 for row in session.query(AverageSale).all())


def test_delete_tank_volume(
    session: Session,
    client: TestClient,
    add_tank_volume: AddTankVolumeFunction,
):
    add_tank_volume(datetime(2023, 1, 1, 10, 0), 10)
    id2 = add_tank_volume(datetime(2023, 1, 3, 10, 0), 20)
    assert session.query(AverageSale).count() > 0

    response = client.delete(f"/tanks/1/volumes/{id2}")

    assert response.status_code == 204
    assert session.query(AverageSale).count() == 0
