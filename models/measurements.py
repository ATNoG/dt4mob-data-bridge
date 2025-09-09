from datetime import datetime
from pydantic import BaseModel, Field, field_serializer


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
