from typing import Optional, Union
from pydantic import BaseModel, Field

from models.geo import Point


class Light(BaseModel):
    object_id: Union[int, str] = Field(alias="OBJECTID")
    type: str
    estado: Optional[str] = None
    codiparmario: Optional[str] = None
    codipcoluna: Optional[str] = None
    tipoiluminacao: Optional[str] = None
    pontosdeluz: Optional[str] = None
    tipotecnologia: Optional[str] = None
    alturacoluna: Optional[str] = None
    tipocoluna: Optional[str] = None
    tipofixacao: Optional[str] = None
    material: Optional[str] = None
    tipoacabamento: Optional[str] = None
    potenciallampadas: Optional[str] = None
    tipodisprotecao: Optional[str] = None
    localizacao: Optional[str] = None
    posicao: Optional[str] = None
    distancia_: Optional[float] = None
    observacoes: Optional[str] = None
    via: Optional[str] = None
    km: Optional[str] = None
    unidadegestora: Optional[str] = None
    distrito: Optional[str] = None
    concelho: Optional[str] = None
    utilizador: Optional[str] = None
    dataregisto: Optional[str] = None
    datacolocacao: Optional[str] = None
    data_sistema: Optional[str] = None
    created_user: Optional[str] = None
    created_date: Optional[str] = None
    last_edited_user: Optional[str] = None
    last_edited_date: Optional[str] = None
    validacao: Optional[str] = None
    gestao: Optional[str] = None
    condicao_ativo: Optional[str] = None
    SOCARTO: Optional[str] = None
    location: Point
    geotile: int
