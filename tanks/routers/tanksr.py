import sqlalchemy
from fastapi import APIRouter

from ..crud import CollectionResource, SQLModelCRUD
from ..dependencies import Session
from ..models import Tank
from ..schemas import BaseTank

router = APIRouter(prefix="/tanks")


def crud(session: Session) -> SQLModelCRUD[Tank, BaseTank]:
    return SQLModelCRUD[Tank, BaseTank](session, Tank)


@router.post("/", status_code=201)
def create(session: Session, tank: BaseTank) -> Tank:
    return crud(session).create(tank)


@router.get("/{tank_id}")
def get_one(session: Session, tank_id: int) -> Tank:
    return crud(session).get_one(tank_id)


@router.get("/")
def get_many(session: Session, offset: int, limit: int) -> CollectionResource[Tank]:
    return crud(session).get_many(offset=offset, limit=limit)


@router.put("/{tank_id}")
def update(session: Session, tank_id: int, tank: BaseTank) -> Tank:
    deleted_rows = session.query(Tank).filter_by(id=tank_id).delete()

    if deleted_rows == 0:
        raise sqlalchemy.exc.NoResultFound()

    tank = Tank(id=tank_id, **tank.dict())
    session.add(tank)
    session.commit()

    return tank


@router.delete("/{tank_id}", status_code=204)
def delete(session: Session, tank_id: int):
    deleted_rows = session.query(Tank).filter_by(id=tank_id).delete()

    if deleted_rows == 0:
        raise sqlalchemy.exc.NoResultFound()
