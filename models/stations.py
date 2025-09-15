from pydantic import BaseModel
from models.measurements import Measurement


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
