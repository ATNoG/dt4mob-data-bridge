from enum import Enum
from datetime import datetime
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


class RoadClosedType(str, Enum):
    ROAD_CLOSED = "ROAD_CLOSED_EVENT"


class PoliceType(str, Enum):
    HIDING = "POLICE_HIDING"
    CAMERA = "POLICE_WITH_MOBILE_CAMERA"


AlertSubtype = Union[JamType, HazardType, PoliceType, RoadClosedType, Literal[""]]


class Alert(BaseModel):
    country: str = "PO"
    city: Optional[str] = None
    street: Optional[str] = None
    confidence: int
    reliability: int
    type: str
    speed: float
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
    severity: int
    country: str
    level: int
    city: str
    geometry: PolyLine
    speedKMH: float
    length: int
    roadType: int
    street: str
    pubMillis: datetime

    @field_serializer("pubMillis")
    def serialize_timestamp(self, dt: datetime) -> int:
        return int(dt.timestamp() * 100)


class WazeRequest(BaseModel):
    startTimeMillis: datetime
    endTimeMillis: datetime
    alerts: List[Alert] = []
    jams: List[Jam] = []

    @field_serializer("startTimeMillis", "endTimeMillis")
    def serialize_timestamp(self, dt: datetime) -> int:
        return int(dt.timestamp() * 100)
