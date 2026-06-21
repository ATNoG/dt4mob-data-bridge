from datetime import datetime, timezone, timedelta
from enum import Enum

from pydantic import BaseModel, Field, field_serializer, field_validator

from models.geo import Point


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


class AwarenessLevel(str, Enum):
    GRAY = "gray"
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


class AwarenessType(str, Enum):
    SEA_AGITATION = "Agitação Marítima"
    SNOW = "Neve"
    FOG = "Nevoeiro"
    RAIN = "Precipitação"
    COLD = "Tempo Frio"
    HOT = "Tempo Quente"
    THUNDER = "Trovoada"
    WIND = "Vento"


class WarningArea(BaseModel):
    region_id: int = Field(alias="idRegiao")
    warning_area: str = Field(alias="idAreaAviso")
    municipality_id: int = Field(alias="idConcelho")
    district_id: int = Field(alias="idDistrito")
    latitude: float = Field(alias="latitude")
    longitude: float = Field(alias="longitude")
    region_name: str = Field(alias="local")


class Warning(BaseModel):
    text: str
    awareness_type: AwarenessType = Field(alias="awarenessTypeName")
    awareness_level: AwarenessLevel = Field(alias="awarenessLevelID")
    warning_area: str = Field(alias="idAreaAviso")
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")

    @field_serializer("start_time", "end_time")
    def serialize_timestamp(self, dt: datetime) -> int:
        return int(dt.timestamp() * 100)

    @field_validator("start_time", "end_time", mode="before")
    def parse_datetime(cls, value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=timezone.utc
        )


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
    def serialize_time(self, time: datetime) -> str:
        return time.isoformat()


class Station(BaseModel, frozen=True):
    id: int
    location: Point
    location_name: str
    geotile: int
    expiry_ts: datetime

    @field_serializer("expiry_ts")
    def serialize_time(self, time: datetime) -> str:
        return time.isoformat()

    def create_message(self, measurement: Measurement) -> dict[str, object]:
        return {
            "attributes": self.model_dump(),
            "features": {"measurements": {"properties": measurement.model_dump()}},
        }
