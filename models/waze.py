from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, field_serializer

from models.geo import Point, PolyLine


class AlertType(str, Enum):
    POLICE = "POLICE"
    ROAD_CLOSED = "ROAD_CLOSED"
    HAZARD = "HAZARD"
    JAM = "JAM"
    ACCIDENT = "ACCIDENT"


class JamType(str, Enum):
    STAND_STILL = "JAM_STAND_STILL_TRAFFIC"
    HEAVY = "JAM_HEAVY_TRAFFIC"


class HazardType(str, Enum):
    ON_ROAD = "HAZARD_ON_ROAD"
    CAR_STOPPED = "HAZARD_ON_SHOULDER_CAR_STOPPED"
    ON_ROAD_CONSTRUCTION = "HAZARD_ON_ROAD_CONSTRUCTION"
    OBJECT = "HAZARD_ON_ROAD_OBJECT"
    POT_HOLE = "HAZARD_ON_ROAD_POT_HOLE"
    WEATHER = "HAZARD_WEATHER"
    ROAD_LANE_CLOSED = "HAZARD_ON_ROAD_LANE_CLOSED"


class RoadClosedType(str, Enum):
    ROAD_CLOSED = "ROAD_CLOSED_EVENT"


class PoliceType(str, Enum):
    HIDING = "POLICE_HIDING"
    CAMERA = "POLICE_WITH_MOBILE_CAMERA"


AlertSubtype = Union[JamType, HazardType, PoliceType, RoadClosedType, Literal[""]]


class Alert(BaseModel):
    id: str
    country: str = "PO"
    city: Optional[str] = None
    street: Optional[str] = None
    type: str
    location: Point
    subtype: AlertSubtype
    pubMillis: datetime

    @field_serializer("pubMillis")
    def serialize_timestamp(self, dt: datetime) -> int:
        return int(dt.timestamp() * 100)

    @field_serializer("subtype")
    def serialize_subtype(self, subtype: AlertSubtype) -> str:
        return str(subtype)


class Jam(BaseModel):
    id: int
    line: PolyLine
    level: int
    street: str
    city: str
    updateMillis: Optional[datetime] = None
    length: int
    speed: float

    @field_serializer("updateMillis")
    def serialize_timestamp(self, dt: datetime | None) -> int | None:
        if dt:
            return int(dt.timestamp() * 100)
        return None


class WazeRequest(BaseModel):
    alerts: List[Alert] = []
    jams: List[Jam] = []
    geotile: int
