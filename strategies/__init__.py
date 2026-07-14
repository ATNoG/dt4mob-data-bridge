from typing import Annotated, List, Literal, Self, Union

from loguru import logger
from pydantic import BaseModel, Field, model_validator

from strategies.geojson import GeoJsonStrategy
from strategies.meteo import MeteoStrategy, WarningsStrategy
from strategies.strategy import BaseStrategy
from strategies.traffic import TrafficStrategy


class _BaseType(BaseModel):
    type: str
    namespace: str


class _Meteo(_BaseType):
    type: Literal["meteo"] = "meteo"


class _MeteoWarnings(_BaseType):
    type: Literal["meteo_warnings"] = "meteo_warnings"


class _Traffic(_BaseType):
    type: Literal["traffic"] = "traffic"
    sensor_name: str
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


StrategyType = Annotated[
    Union[_Meteo, _Traffic, _GeoJson, _MeteoWarnings], Field(discriminator="type")
]


def _type_to_strategy(
    type: StrategyType,
    policyId: str,
    subject: str,
) -> BaseStrategy:
    match type:
        case _Meteo():
            return MeteoStrategy(subject, type.namespace, policyId)
        case _MeteoWarnings():
            return WarningsStrategy(subject, type.namespace, policyId)
        case _Traffic():
            return TrafficStrategy(
                subject,
                type.namespace,
                policyId,
                type.sensor_name,
                type.road,
                type.latitude,
                type.longitude,
            )
        case _GeoJson():
            return GeoJsonStrategy(
                subject, type.namespace, policyId, type.dir, type.file
            )


def acquire_strategies(
    strategies: List[StrategyType],
    policyId: str,
    subject: str,
) -> List[BaseStrategy]:
    logger.debug("Acquiring strategies {} for policyId {}", strategies, policyId)
    ret = [_type_to_strategy(s, policyId, subject) for s in strategies]
    logger.debug("Acquired strategies {}", ret)
    return ret
