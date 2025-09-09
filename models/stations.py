from enum import Enum
from pydantic import BaseModel
from models.measurements import Measurement
from settings import settings


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


class Station(BaseModel, frozen=True):
    id: int
    latitude: float
    longitude: float
    location: str

    def create_message(self, measurement: Measurement) -> dict:
        return {
            "topic": f"{settings.hono.device_id}/{self.id}/things/twin/commands/modify",
            "path": "/",
            "headers": {},
            "value": {
                "policyId": settings.hono.policy_id,
                "attributes": self.model_dump(),
                "features": {"metereology": {"properties": measurement.model_dump()}},
            },
        }
