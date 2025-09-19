from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_serializer


class WindDirection(int, Enum):
    NORTH_WEST = 8
    WEST = 7
    SOUTH_WEST = 6
    SOUTH = 5
    SOUTH_EAST = 4
    EAST = 3
    NORTH_EAST = 2
    NORTH = 1
    UNKNOWN = 0


class Measurement(BaseModel):
    wind_intensity: float = Field(alias="intensidadeVentoKM")
    temperature: float = Field(alias="temperatura")
    radiation: float = Field(alias="radiacao")
    wind_direction: WindDirection = Field(alias="idDireccVento")
    accumulated_precipitation: float = Field(alias="precAcumulada")
    pressure: float = Field(alias="pressao")
    humidity: int = Field(alias="humidade")
    time: datetime

    @field_serializer("time")
    def serialize_time(self, time: datetime):
        return time.isoformat()


class Station(BaseModel, frozen=True):
    id: int
    latitude: float
    longitude: float
    location: str

    def create_message(self, measurement: Measurement) -> dict:
        return {
            "attributes": self.model_dump(),
            "features": {"metereology": {"properties": measurement.model_dump()}},
        }
