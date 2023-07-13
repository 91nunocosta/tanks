from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Type

from pytest import fixture, raises
from sqlmodel import Session

from tanks.hooks.avgsales_updater import AvgSalesUpdater
from tanks.models import AverageSale
from tanks.schemas import Sale

from ..conftest import CreateDBRowsFunction
from ..helpers import BaseTestCase, parametrize

TANK_ID = 1


@fixture(name="avgsales_updater")
def sales_fixture(session: Session) -> AvgSalesUpdater:
    return AvgSalesUpdater(session)


@fixture(name="five_saturdays")
def five_saturdays_fixture() -> list[date]:
    return [
        datetime(2023, 1, 1),
        datetime(2023, 1, 8),
        datetime(2023, 1, 15),
        datetime(2023, 1, 22),
        datetime(2023, 1, 29),
    ]


CreateSalesFunction = Callable[[list[float]], list[AverageSale]]


@fixture(name="create_sales")
def create_sales_fixture(
    create_db_rows: CreateDBRowsFunction, five_saturdays: list[date]
) -> CreateSalesFunction:
    def create_sales(sales: list[float]) -> list[AverageSale]:
        if not sales:
            return []

        def average_sales(tank_id: int) -> list[AverageSale]:
            return [
                AverageSale(
                    id=None,
                    tank_id=tank_id,
                    date=day,
                    sales=len(sales),
                    total=sum(sales),
                )
                for day in five_saturdays
            ]

        return create_db_rows(
            *(average_sales(tank_id=TANK_ID) + average_sales(tank_id=TANK_ID + 1))
        )

    return create_sales


def assert_avg_sales_equal(
    session: Session, dates: list[datetime], sales: int, total: float, average: float
) -> None:
    query = session.query(AverageSale).filter_by(tank_id=TANK_ID)
    for day in dates:
        entry: AverageSale | None = query.filter_by(date=day.date()).first()
        assert entry is not None, day
        assert entry.sales == sales
        assert entry.total == total
        assert entry.average == average


@dataclass
class TestCase(BaseTestCase):
    existing_sales: list[float]
    quantity: float
    expected_rows_count: int
    expected_sales: int
    expected_total: float
    expected_average: float
    expected_error: Type[Exception] | None


@parametrize(
    TestCase(
        name="first sale",
        existing_sales=[],
        quantity=10,
        expected_rows_count=5,
        expected_sales=1,
        expected_total=10,
        expected_average=10,
        expected_error=None,
    ),
    TestCase(
        name="second sale",
        existing_sales=[10],
        quantity=20,
        expected_rows_count=5,
        expected_sales=2,
        expected_total=30,
        expected_average=15,
        expected_error=None,
    ),
    TestCase(
        name="sale of 0",
        existing_sales=[10],
        quantity=0,
        expected_rows_count=5,
        expected_sales=1,
        expected_total=10,
        expected_average=10,
        expected_error=ValueError,
    ),
    TestCase(
        name="sale of -1",
        existing_sales=[10],
        quantity=-1,
        expected_rows_count=5,
        expected_sales=1,
        expected_total=10,
        expected_average=10,
        expected_error=ValueError,
    ),
)
def test_add_sale(
    session: Session,
    five_saturdays: list[datetime],
    create_sales: CreateSalesFunction,
    avgsales_updater: AvgSalesUpdater,
    case: TestCase,
):
    create_sales(case.existing_sales)

    sale = Sale(tank_id=TANK_ID, created_at=five_saturdays[0], quantity=case.quantity)

    if case.expected_error:
        with raises(case.expected_error):
            avgsales_updater.handle_added_sale(sale)
    else:
        avgsales_updater.handle_added_sale(sale)

    assert (
        session.query(AverageSale).filter_by(tank_id=TANK_ID).count()
        == case.expected_rows_count
    )

    assert_avg_sales_equal(
        session=session,
        dates=five_saturdays,
        sales=case.expected_sales,
        total=case.expected_total,
        average=case.expected_average,
    )


@parametrize(
    TestCase(
        name="one sale",
        existing_sales=[10, 10],
        quantity=10,
        expected_rows_count=5,
        expected_sales=1,
        expected_total=10,
        expected_average=10,
        expected_error=None,
    ),
    TestCase(
        name="the single existing sale",
        existing_sales=[20],
        quantity=20,
        expected_rows_count=0,
        expected_sales=0,
        expected_total=0,
        expected_average=0,
        expected_error=None,
    ),
    TestCase(
        name="sale of 0",
        existing_sales=[10],
        quantity=0,
        expected_rows_count=5,
        expected_sales=1,
        expected_total=10,
        expected_average=10,
        expected_error=ValueError,
    ),
    TestCase(
        name="sale of -1",
        existing_sales=[10],
        quantity=-1,
        expected_rows_count=5,
        expected_sales=1,
        expected_total=10,
        expected_average=10,
        expected_error=ValueError,
    ),
    TestCase(
        name="non existing sale",
        existing_sales=[],
        quantity=10,
        expected_rows_count=0,
        expected_sales=0,
        expected_total=0,
        expected_average=0,
        expected_error=ValueError,
    ),
    TestCase(
        name="more than total sales",
        existing_sales=[20],
        quantity=40,
        expected_rows_count=5,
        expected_sales=1,
        expected_total=20,
        expected_average=20,
        expected_error=ValueError,
    ),
    TestCase(
        name="single sale smaller than the only existing sale",
        existing_sales=[20],
        quantity=40,
        expected_rows_count=5,
        expected_sales=1,
        expected_total=20,
        expected_average=20,
        expected_error=ValueError,
    ),
    TestCase(
        name="sale equal to the total of 2 sales",
        existing_sales=[20, 20],
        quantity=40,
        expected_rows_count=5,
        expected_sales=2,
        expected_total=40,
        expected_average=20,
        expected_error=ValueError,
    ),
    TestCase(
        name="sale bigger than total sales",
        existing_sales=[20, 20],
        quantity=80,
        expected_rows_count=5,
        expected_sales=2,
        expected_total=40,
        expected_average=20,
        expected_error=ValueError,
    ),
)
def test_delete(
    session: Session,
    five_saturdays: list[datetime],
    create_sales: CreateSalesFunction,
    avgsales_updater: AvgSalesUpdater,
    case: TestCase,
):
    create_sales(case.existing_sales)

    sale = Sale(tank_id=TANK_ID, created_at=five_saturdays[0], quantity=case.quantity)

    if case.expected_error:
        with raises(case.expected_error):
            avgsales_updater.handle_deleted_sale(sale)

    else:
        avgsales_updater.handle_deleted_sale(sale)

    assert (
        session.query(AverageSale).filter_by(tank_id=TANK_ID).count()
        == case.expected_rows_count
    )

    if case.expected_rows_count > 0:
        assert_avg_sales_equal(
            session=session,
            dates=five_saturdays,
            sales=case.expected_sales,
            total=case.expected_total,
            average=case.expected_average,
        )


def test_inconsistent_delete(
    session: Session,
    five_saturdays: list[datetime],
    create_sales: CreateSalesFunction,
    avgsales_updater: AvgSalesUpdater,
):
    sales = create_sales([10])

    sales[2].total = 20

    sale = Sale(tank_id=TANK_ID, created_at=five_saturdays[0], quantity=10)

    with raises(ValueError):
        avgsales_updater.handle_deleted_sale(sale)

    assert session.query(AverageSale).filter_by(tank_id=TANK_ID).count() == 5

    sales[2].total = 10

    assert_avg_sales_equal(
        session=session,
        dates=five_saturdays,
        sales=1,
        total=10,
        average=10,
    )
