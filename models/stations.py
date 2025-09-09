from pydantic import BaseModel
from models.measurements import Measurement
from settings import settings


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
