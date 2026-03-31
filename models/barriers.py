from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import List, Optional

from models.geo import Point


class EstadoBarreira(int, Enum):
    UNKNOWN = 0
    SUFICIENTE = 1
    INSUFICIENTE = 2


class Fabricante(int, Enum):
    UNKNOWN = 0
    METALOGALVA = 1
    ASEBAL = 2
    HIASA = 3
    OUTROS = 4
    NAO_IDENTIFICAVEL = 5


class NContencao(int, Enum):
    UNKNOWN = 0
    T1 = 1
    T2 = 2
    T3 = 3
    N1 = 4
    N2 = 5
    H1 = 6
    L1 = 7
    H2 = 8
    L2 = 9
    H3 = 10
    L3 = 11
    H4A = 12
    H4B = 13
    L4A = 14
    L4B = 15
    NAO_IDENTIFICAVEL = 16


class LUtil(int, Enum):
    UNKNOWN = 0
    W1 = 1
    W2 = 2
    W3 = 3
    W4 = 4
    W5 = 5
    W6 = 6
    W7 = 7
    W8 = 8
    NAO_IDENTIFICAVEL = 9


class Localizacao(int, Enum):
    UNKNOWN = 0
    PLENA_VIA = 1
    INTERSECAO_NIVEL = 2
    NO_LIGACAO = 3
    OBRA_ARTE = 4


class PosicaoVia(int, Enum):
    UNKNOWN = 0
    Berma_direita = 1
    Berma_esquerda = 2
    Central = 3
    Berma_central_direita = 4
    Berma_central_esquerda = 5


class AlturaBS(int, Enum):
    UNKNOWN = 0
    Menor_igual_0_5 = 1
    Maior_0_5_menor_igual_0_6 = 2
    Maior_0_6_menor_igual_0_8 = 3
    Maior_0_8_menor_igual_1_0 = 4
    Maior_1_0 = 5


class DistPrumos(int, Enum):
    UNKNOWN = 0
    M_4_00 = 1
    M_2_00 = 2
    M_1_33 = 3
    Outro_valor = 4


class DPM(int, Enum):
    UNKNOWN = 0
    Prot_continua_viga = 1
    Prot_indiv_prumo_a_prumo = 2
    Nao_aplicavel = 3


class Barrier(BaseModel):
    objectID: int = Field(alias="OBJECTID")
    estado_barreira: EstadoBarreira
    tipo_barreira: str
    fabricante: Fabricante
    n_contencao: NContencao
    n_larg_util: LUtil
    localizacao: Optional[Localizacao]
    posicao_via: PosicaoVia
    alt_guarda: AlturaBS
    dist_prumos: DistPrumos
    drenagem_assoc: bool
    dpm: DPM
    numero_barreiras: Optional[int]
    kmi: Optional[float]
    kmf: Optional[float]
    distrito: str
    concelho: str
    obra_de_arte: bool
    condicao_ativo: bool
    geometry: List[Point]
    geotile: int

    @field_validator("drenagem_assoc", "obra_de_arte", "condicao_ativo", mode="before")
    @classmethod
    def booleans(cls, value: int) -> bool:
        return value == 1

    @field_validator(
        "fabricante",
        "n_contencao",
        "n_larg_util",
        "dpm",
        "dist_prumos",
        "alt_guarda",
        "posicao_via",
        "localizacao",
        "numero_barreiras",
        mode="before",
    )
    @classmethod
    def str_to_int(cls, value: str) -> Optional[int]:
        try:
            return int(value)
        except ValueError:
            return None
