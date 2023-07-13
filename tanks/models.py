import datetime

from sqlmodel import Field, SQLModel

from .schemas import BaseTank, BaseTankVolume


class Tank(SQLModel, BaseTank, table=True):
    id: int | None = Field(primary_key=True)


class TankVolume(SQLModel, BaseTankVolume, table=True):
    id: int | None = Field(primary_key=True)
    tank_id: int = Field(foreign_key=Tank.id)
    created_at: datetime.datetime = Field(index=True)


class Thank(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
