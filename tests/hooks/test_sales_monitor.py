from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from pytest import fixture
from sqlmodel import Session

from tanks.hooks.sales_monitor import (
    SalesMonitor,
    SalesObserver,
    get_contiguous_volumes,
)
from tanks.models import Tank, TankVolume
from tanks.schemas import Sale

from ..conftest import CreateDBRowsFunction
from ..helpers import BaseTestCase, parametrize

TANK_ID = 1


class SalesFake(SalesObserver):
    def __init__(self, count: int = 0, total: float = 0.0):
        self.count = count
        self.total = total

    def handle_added_sale(self, sale: Sale) -> None:
        print(f"Adding {sale}.")
        self.count += 1
        self.total += sale.quantity

    def handle_deleted_sale(self, sale: Sale) -> None:
        print(f"Deleting {sale}.")
        self.count -= 1
        self.total -= sale.quantity


CreateTankVolumesFunction = Callable[[list[float]], list[TankVolume]]


@fixture(name="create_tank_volumes")
def create_tank_volumes_fixture(
    create_db_rows: CreateDBRowsFunction,
) -> CreateTankVolumesFunction:
    create_db_rows(Tank(id=1, name="USL Diesel"))

    def create_tank_volumes(volumes: list[float]) -> list[TankVolume]:
        return create_db_rows(
            *[
                TankVolume(
                    id=len(volumes) - i,
                    tank_id=1,
                    created_at=datetime(2023, 1, 1, 10, 0) + timedelta(days=2 * i),
                    volume=volume,
                )
                for i, volume in enumerate(volumes)
            ]
        )

    return create_tank_volumes


@dataclass
class GCVTestCase(BaseTestCase):
    datetimes: list[datetime]
    position: int
    expected_previous_position: int
    expected_next_position: int


NONE = -1
FIVE_SEQUENTIAL_DAYS = [datetime(2023, 1, i + 1) for i in range(5)]


@parametrize(
    GCVTestCase(
        name="first",
        datetimes=FIVE_SEQUENTIAL_DAYS,
        position=0,
        expected_previous_position=NONE,
        expected_next_position=1,
    ),
    GCVTestCase(
        name="middle",
        datetimes=FIVE_SEQUENTIAL_DAYS,
        position=2,
        expected_previous_position=1,
        expected_next_position=3,
    ),
    GCVTestCase(
        name="last",
        datetimes=FIVE_SEQUENTIAL_DAYS,
        position=4,
        expected_previous_position=3,
        expected_next_position=NONE,
    ),
    GCVTestCase(
        name="middle on same day",
        datetimes=[datetime(2023, 1, 1, 10 + i) for i in range(5)],
        position=2,
        expected_previous_position=1,
        expected_next_position=3,
    ),
)
def test_get_contiguous_volumes(
    session: Session,
    create_db_rows: CreateDBRowsFunction,
    case: GCVTestCase,
):
    tank_volumes: list[TankVolume] = create_db_rows(
        *[
            TankVolume(id=None, tank_id=TANK_ID, created_at=dt, volume=i)
            for i, dt in enumerate(case.datetimes)
        ]
    )
    tank_volume = tank_volumes[case.position]
    # None is denoted by NONE=-1 in the argvalues above
    tank_volumes.append(None)  # type: ignore

    assert get_contiguous_volumes(session=session, tank_volume=tank_volume) == (
        tank_volumes[case.expected_previous_position],
        tank_volumes[case.expected_next_position],
    )


@dataclass
class TestCase(BaseTestCase):
    name: str
    volumes: list[float]
    sales_fake: SalesFake
    handled: int
    expected_sales: int
    expected_total: float


@parametrize(
    TestCase(
        name="beginning",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(1, 10),
        handled=0,
        expected_sales=2,
        expected_total=20,
    ),
    TestCase(
        name="middle",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(1, 20),
        handled=1,
        expected_sales=2,
        expected_total=20,
    ),
    TestCase(
        name="end",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(1, 10),
        handled=2,
        expected_sales=2,
        expected_total=20,
    ),
    TestCase(
        name="on decreasing volumes",
        volumes=[30, 20, 10],
        sales_fake=SalesFake(0, 0),
        handled=0,
        expected_sales=0,
        expected_total=0,
    ),
    TestCase(
        name="on increasing and decreasing volumes",
        volumes=[10, 30, 20],
        sales_fake=SalesFake(1, 10),
        handled=1,
        expected_sales=1,
        expected_total=20,
    ),
)
def test_handle_volume_added(
    session: Session,
    create_tank_volumes: CreateTankVolumesFunction,
    case: TestCase,
):
    tank_volumes = create_tank_volumes(case.volumes)

    handler = SalesMonitor(session, case.sales_fake)
    handler.handle_added_tank_volume(tank_volumes[case.handled])

    assert case.sales_fake.count == case.expected_sales
    assert case.sales_fake.total == case.expected_total


@parametrize(
    TestCase(
        name="beginning",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(2, 20),
        handled=0,
        expected_sales=1,
        expected_total=10,
    ),
    TestCase(
        name="middle",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(2, 20),
        handled=1,
        expected_sales=1,
        expected_total=20,
    ),
    TestCase(
        name="end",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(2, 20),
        handled=2,
        expected_sales=1,
        expected_total=10,
    ),
    TestCase(
        name="on decreasing volumes",
        volumes=[30, 20, 10],
        sales_fake=SalesFake(0, 0),
        handled=0,
        expected_sales=0,
        expected_total=0,
    ),
    TestCase(
        name="on increasing and decreasing volumes",
        volumes=[10, 30, 20],
        sales_fake=SalesFake(1, 20),
        handled=1,
        expected_sales=1,
        expected_total=10,
    ),
    TestCase(
        name="on decreasing and increasing volumes",
        volumes=[30, 10, 20],
        sales_fake=SalesFake(1, 10),
        handled=1,
        expected_sales=0,
        expected_total=0,
    ),
)
def test_handle_volume_deleted(
    session: Session, create_tank_volumes: CreateTankVolumesFunction, case: TestCase
):
    tank_volumes = create_tank_volumes(case.volumes)

    handler = SalesMonitor(session, case.sales_fake)
    handler.handle_deleted_tank_volume(tank_volumes[case.handled])

    assert case.sales_fake.count == case.expected_sales
    assert case.sales_fake.total == case.expected_total


@dataclass
class UpdateTestCase(TestCase):
    old_volume: float


@parametrize(
    UpdateTestCase(
        name="beginning up",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(2, 25),
        handled=0,
        old_volume=5,
        expected_sales=2,
        expected_total=20,
    ),
    UpdateTestCase(
        name="beginning down",
        volumes=[5, 20, 30],
        sales_fake=SalesFake(2, 20),
        handled=0,
        old_volume=10,
        expected_sales=2,
        expected_total=25,
    ),
    UpdateTestCase(
        name="middle up",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(2, 20),
        handled=1,
        old_volume=15,
        expected_sales=2,
        expected_total=20,
    ),
    UpdateTestCase(
        name="middle down",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(2, 20),
        handled=1,
        old_volume=25,
        expected_sales=2,
        expected_total=20,
    ),
    UpdateTestCase(
        name="end up",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(2, 15),
        handled=2,
        old_volume=25,
        expected_sales=2,
        expected_total=20,
    ),
    UpdateTestCase(
        name="end down",
        volumes=[10, 20, 30],
        sales_fake=SalesFake(2, 25),
        handled=2,
        old_volume=35,
        expected_sales=2,
        expected_total=20,
    ),
    UpdateTestCase(
        name="on decreasing volumes",
        volumes=[30, 20, 10],
        sales_fake=SalesFake(0, 0),
        handled=0,
        old_volume=25,
        expected_sales=0,
        expected_total=0,
    ),
    UpdateTestCase(
        name="triggering sale addition",
        volumes=[10, 30, 20],
        sales_fake=SalesFake(0, 0),
        handled=0,
        old_volume=40,
        expected_sales=1,
        expected_total=20,
    ),
    UpdateTestCase(
        name="triggering sale removal",
        volumes=[30, 20, 10],
        sales_fake=SalesFake(1, 10),
        handled=1,
        old_volume=40,
        expected_sales=0,
        expected_total=0,
    ),
)
def test_handle_tank_volume_updated(
    session: Session,
    create_tank_volumes: CreateTankVolumesFunction,
    case: UpdateTestCase,
):
    tank_volumes = create_tank_volumes(case.volumes)

    handler = SalesMonitor(session, case.sales_fake)
    new_tank_volume = tank_volumes[case.handled]
    handler.handle_updated_tank_volume(
        new_tank_volume=new_tank_volume, old_volume=case.old_volume
    )

    assert case.sales_fake.count == case.expected_sales
    assert case.sales_fake.total == case.expected_total
