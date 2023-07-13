from typing import Protocol

from sqlmodel import Session, asc, desc

from tanks.models import TankVolume
from tanks.schemas import Sale


class SalesObserver(Protocol):
    def handle_added_sale(self, sale: Sale) -> None:
        ...  # pragma: no cover

    def handle_deleted_sale(self, sale: Sale) -> None:
        ...  # pragma: no cover


def get_contiguous_volumes(
    session: Session, tank_volume: TankVolume
) -> tuple[TankVolume | None, TankVolume | None]:
    query = session.query(TankVolume).filter_by(tank_id=tank_volume.tank_id)
    previous_volume = (
        query.filter(TankVolume.created_at < tank_volume.created_at)
        .order_by(desc(TankVolume.created_at))
        .limit(1)
    ).first()

    next_volume = (
        query.filter(TankVolume.created_at > tank_volume.created_at)
        .order_by(asc(TankVolume.created_at))
        .limit(1)
    ).first()

    return (previous_volume, next_volume)


class SalesMonitor:
    def __init__(self, session: Session, avgsales_updater: SalesObserver):
        self._session = session
        self._sales_observable = avgsales_updater

    def handle_added_tank_volume(self, tank_volume: TankVolume) -> None:
        previous_volume, next_volume = get_contiguous_volumes(
            session=self._session, tank_volume=tank_volume
        )

        def sale(value: float):
            return Sale(
                tank_id=tank_volume.tank_id,
                created_at=tank_volume.created_at,
                quantity=value,
            )

        if (
            previous_volume
            and next_volume
            and previous_volume.volume < next_volume.volume
        ):
            value = next_volume.volume - previous_volume.volume
            self._sales_observable.handle_deleted_sale(sale(value))

        if previous_volume is not None and previous_volume.volume < tank_volume.volume:
            value = tank_volume.volume - previous_volume.volume
            self._sales_observable.handle_added_sale(sale(value))

        if next_volume is not None and tank_volume.volume < next_volume.volume:
            value = next_volume.volume - tank_volume.volume
            self._sales_observable.handle_added_sale(sale(value))

    def handle_deleted_tank_volume(self, tank_volume: TankVolume) -> None:
        previous_volume, next_volume = get_contiguous_volumes(
            session=self._session, tank_volume=tank_volume
        )

        def sale(value: float):
            return Sale(
                tank_id=tank_volume.tank_id,
                created_at=tank_volume.created_at,
                quantity=value,
            )

        if previous_volume and previous_volume.volume < tank_volume.volume:
            value = tank_volume.volume - previous_volume.volume
            self._sales_observable.handle_deleted_sale(sale(value))

        if next_volume and tank_volume.volume < next_volume.volume:
            value = next_volume.volume - tank_volume.volume
            self._sales_observable.handle_deleted_sale(sale(value))

        if (
            previous_volume
            and next_volume
            and previous_volume.volume < next_volume.volume
        ):
            value = next_volume.volume - previous_volume.volume
            self._sales_observable.handle_added_sale(sale(value))

    def handle_updated_tank_volume(
        self, new_tank_volume: TankVolume, old_volume: float
    ) -> None:
        old_tank_volume = TankVolume(**new_tank_volume.dict())
        old_tank_volume.volume = old_volume
        self.handle_deleted_tank_volume(old_tank_volume)
        self.handle_added_tank_volume(new_tank_volume)
