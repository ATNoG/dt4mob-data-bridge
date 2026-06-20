from typing import Any

from pydantic import BaseModel


class _Geometry(BaseModel):
    type: str
    coordinates: list[Any]


class _Features(BaseModel):
    type: str
    properties: dict[str, Any]
    geometry: _Geometry


class GeoJSON(BaseModel):
    type: str
    name: str
    crs: dict[str, Any]
    features: list[_Features]
