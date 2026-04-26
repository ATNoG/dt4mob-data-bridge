from pydantic import BaseModel, Field
from models.geo import Point


class LightPoint(BaseModel):
    object_id: int = Field(alias="OBJECTID")
    estado: str
    pontosdeluz: str
    alturacoluna: str
    tipocoluna: str
    tipofixacao: str
    material: str
    tipoacabamento: str
    potenciallampadas: str
    tipodisprotecao: str
    localizacao: str
    posicao: str
    gestao: str
    via: str
    concelho: str
    distrito: str
    distancia: float = Field(alias="distancia_")
    geometry: Point
