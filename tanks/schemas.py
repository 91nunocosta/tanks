from datetime import datetime

from pydantic import BaseModel


class BaseTank(BaseModel):
    name: str


class BaseTankVolume(BaseModel):
    volume: float


class TankVolumePatch(BaseModel):
    volume: float


class Sale(BaseModel):
    tank_id: int
    quantity: float
    created_at: datetime
