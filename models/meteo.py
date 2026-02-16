from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_serializer
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


class WarningArea(str, Enum):
    CENTRAL_AZORES = "ACE"
    WEST_AZORES = "AOC"
    EAST_AZORES = "AOR"
    AVEIRO = "AVR"
    BRAGANCA = "BGC"
    BEJA = "BJA"
    BRAGA = "BRG"
    CASTELO_BRANCO = "CBO"
    COIMBRA = "CBR"
    EVORA = "EVR"
    FARO = "FAR"
    GUARDA = "GDA"
    LEIRIA = "LRA"
    LISBOA = "LSB"
    MADEIRA = "MCS"
    PORTO_SANTO = "MPS"
    PORTALEGRE = "PTG"
    PORTO = "PTO"
    SETUBAL = "STB"
    SANTAREM = "STM"
    VIANA_DO_CASTELO = "VCT"
    VISEU = "VIS"
    VILA_REAL = "VRL"


class Warning(BaseModel):
    text: str
    awareness_type: AwarenessType = Field(alias="awarenessTypeName")
    awareness_level: AwarenessLevel = Field(alias="awarenessLevelID")
    warning_area: WarningArea = Field(alias="idAreaAviso")
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")


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

    def create_message(self, measurement: Measurement) -> dict[str, object]:
        return {
            "attributes": self.model_dump(),
            "features": {"metereology": {"properties": measurement.model_dump()}},
        }
