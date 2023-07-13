import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..crud import CollectionResource, SQLModelCRUD
from ..dependencies import SalesMonitor, Session
from ..models import TankVolume
from ..schemas import BaseTankVolume, TankVolumePatch

router = APIRouter(prefix="/tanks/{tank_id}/volumes")

logging.basicConfig(level=logging.ERROR)

_LOGGER = logging.getLogger(__name__)


def _handle_handler_error(err: ValueError):
    _LOGGER.error(
        "Tank volume changes handlers raises error: \n"
        "   %s\n"
        "\n"
        "Database may be in an inconsistent state.",
        err,
    )


def crud(session: Session) -> SQLModelCRUD[TankVolume, BaseTankVolume]:
    return SQLModelCRUD[TankVolume, BaseTankVolume](session, TankVolume)


@router.post("/", status_code=201)
def create(
    session: Session,
    sales_monitor: SalesMonitor,
    tank_id: int,
    tank_volume: BaseTankVolume,
) -> TankVolume:
    created_tank_volume = crud(session).create(
        TankVolume(
            id=None,
            tank_id=tank_id,
            created_at=datetime.now(),
            volume=tank_volume.volume,
        )
    )

    sales_monitor.handle_added_tank_volume(created_tank_volume)

    return created_tank_volume


@router.get("/{tank_volume_id}")
def get_one(session: Session, tank_volume_id: int, tank_id: int) -> TankVolume:
    tank_volume = crud(session).get_one(tank_volume_id)

    if tank_volume.id != tank_id:
        raise HTTPException(status_code=404, detail="Item not found")

    return tank_volume


@router.get("/")
def get_many(
    session: Session, tank_id: int, offset: int, limit: int
) -> CollectionResource[TankVolume]:
    return crud(session).get_many(
        offset=offset, limit=limit, filters={TankVolume.tank_id: tank_id}
    )


@router.patch("/{tank_volume_id}")
def update(
    session: Session,
    tank_id: int,
    tank_volume_id: int,
    patch: TankVolumePatch,
    sales_monitor: SalesMonitor,
) -> TankVolume:
    tank_volume = session.query(TankVolume).filter_by(id=tank_volume_id).one()
    if tank_volume.tank_id != tank_id:
        raise HTTPException(status_code=404, detail="Item not found")

    old_volume = tank_volume.volume

    tank_volume.volume = patch.volume
    session.commit()
    session.refresh(tank_volume)

    try:
        sales_monitor.handle_updated_tank_volume(
            new_tank_volume=tank_volume, old_volume=old_volume
        )
    except ValueError as err:
        _handle_handler_error(err)

    return tank_volume


@router.delete("/{tank_volume_id}", status_code=204)
def delete(
    session: Session,
    tank_id: int,
    tank_volume_id: int,
    sales_monitor: SalesMonitor,
):
    tank_volume = session.query(TankVolume).filter_by(id=tank_volume_id).one()
    if tank_volume.tank_id != tank_id:
        raise HTTPException(status_code=404, detail="Item not found")

    session.query(TankVolume).filter_by(id=tank_volume_id).delete()
    session.commit()

    try:
        sales_monitor.handle_deleted_tank_volume(tank_volume)
    except ValueError as err:
        _handle_handler_error(err)
