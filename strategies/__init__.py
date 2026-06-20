from typing import Annotated, List, Literal, Self, Union

from pydantic import BaseModel, Field, model_validator

from strategies.geojson import GeoJsonStrategy
from strategies.meteo import MeteoStrategy
from strategies.strategy import BaseStrategy
from strategies.traffic import TrafficStrategy


class _BaseType(BaseModel):
    type: str
    subject: str


class _Meteo(_BaseType):
    type: Literal["meteo"] = "meteo"


class _Traffic(_BaseType):
    type: Literal["traffic"] = "traffic"
    sensorName: str
    road: str
    latitude: float
    longitude: float
    radius: float = 1000


class _GeoJson(_BaseType):
    type: Literal["geojson"] = "geojson"
    dir: str | None = None
    file: str | None = None

    @model_validator(mode="after")
    def validate_fields(self) -> Self:
        if (self.dir is None) == (self.file is None):
            raise ValueError(
                "A GeoJson strategy must either have files or directories, not both"
            )
        return self


StrategyType = Annotated[Union[_Meteo, _Traffic, _GeoJson], Field(discriminator="type")]


def _type_to_strategy(
    type: StrategyType,
    policyId: str,
) -> Union[MeteoStrategy, TrafficStrategy, GeoJsonStrategy]:
    match type:
        case _Meteo():
            return MeteoStrategy(type.subject, policyId)
        case _Traffic():
            return TrafficStrategy(
                type.subject,
                policyId,
                type.sensorName,
                type.road,
                type.latitude,
                type.longitude,
            )
        case _GeoJson():
            return GeoJsonStrategy(type.subject, policyId, type.dir, type.file)


def acquire_strategies(
    strategies: List[StrategyType],
    policyId: str,
) -> List[BaseStrategy]:
    return [_type_to_strategy(s, policyId) for s in strategies]
