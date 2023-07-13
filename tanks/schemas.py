from pydantic import BaseModel


class BaseTank(BaseModel):
    name: str


class BaseTankVolume(BaseModel):
    volume: float


class TankVolumePatch(BaseModel):
    volume: float
