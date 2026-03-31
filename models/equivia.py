from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator

from models.geo import Point, PolyLine


class CategoriaVia(int, Enum):
    UNKNOWN = 4
    AUTO_ESTRADA = 5
    IP = 6
    IC = 7
    ER = 8
    EN = 9


class ViaAuxiliar(int, Enum):
    RAMO_ESTRADA = 1
    RAMO_SAIDA = 2
    CAMINHO_PARALELO_ENTRADA = 3
    CAMINHO_PARALELO_SAIDA = 4
    NAO_APLICAVEL = 5


class Posicao(int, Enum):
    DIREITA = 1
    ESQUERDA = 2
    CENTRAL = 3
    CENTRAL_DIREITA = 4
    CENTRAL_ESQUERDA = 5


class TipoVedacao(int, Enum):
    MALHA_PROGRESSIVA = 0
    TIPO_CASSA = 1
    REDE_ENTERRADA = 2
    MALHA_PROGRESSIVA_TIPO_CASSA = 3
    REDE_ENTERRADA_TIPO_CASSA = 4
    OUTRAS = 5


class Gestao(int, Enum):
    IP = 0
    SUBCONCESSAO = 1
    CONCESSAO = 2
    MUNICIPIO = 3


class TipoMaterial(int, Enum):
    BETAO_CIMENTO = 0
    BETAO_BETUMINOSO = 1
    CALCADA = 2
    NAO_PAVIMENTADO = 3
    OUTRO = 4


class Vegetacao(int, Enum):
    ARVORES = 0
    ARBUSTOS = 1
    HERBACEAS = 2
    ARVORES_E_ARBUSTOS = 3
    ARVORES_E_HERBACEAS = 4
    ARBUSTOS_E_HERBACEAS = 5
    ARVORES_ARBUSTOS_E_HERBACEAS = 6
    SEM_VEGETACAO = 7


class EquiviaBase(BaseModel):
    object_id: Union[int, str] = Field(alias="OBJECTID")
    type: str
    equivia_type: str  # Will be set in __init__
    categoria_via: Optional[CategoriaVia] = Field(alias="categoria_da_via")
    posicao: Optional[Posicao]
    location: Union[Point, PolyLine]
    concelho: Optional[str]
    distrito: Optional[str]
    estrada: Optional[str]
    km: Optional[float] = None
    km_ini: Optional[float] = None
    km_fim: Optional[float] = None
    gestao: Optional[Gestao]
    condicao_ativo: Optional[bool]
    geotile: int

    def __init__(self, **data):
        super().__init__(**data)
        # Set equivia_type based on actual subclass
        self.equivia_type = self.__class__.__name__

    @field_validator("condicao_ativo", mode="before")
    @classmethod
    def booleans(cls, value: int) -> bool:
        return value != 0


class AcessosServentias(EquiviaBase):
    largura: float
    tipo_material: TipoMaterial = Field(alias="tipo_de_material")


class DrenagemPontual(EquiviaBase):
    via_auxiliar: ViaAuxiliar
    tipo_material: TipoMaterial = Field(alias="tipo_de_material")
    dimensoes_comprimento: float
    dimensoes_largura: float
    dimensoes_diametro: float


class Iluminação(EquiviaBase):
    tipo_material: TipoMaterial = Field(alias="tipo_de_material")
    n_dispositivos: int
    dispositivos: int


class IntegracaoPaisagistica(EquiviaBase):
    via_auxiliar: ViaAuxiliar
    vegetacao: Vegetacao
    sistema_de_rega: bool

    @field_validator("sistema_de_rega", mode="before")
    @classmethod
    def booleans(cls, value: int) -> bool:
        return value != 0


class MarcoQuilometrico(EquiviaBase):
    via_auxiliar: ViaAuxiliar
    estrada: Optional[str] = Field(alias="n_via")
    tipo: int
    quilometragem: float


class Pavimentos(EquiviaBase):
    largura_inicio: Optional[float]
    largura_fim: Optional[float]
    n_vias_inicio: Optional[float]

    categoria_via: Optional[CategoriaVia] = None
    posicao: Optional[Posicao] = None
    concelho: Optional[str] = None


class Seccoes(EquiviaBase):
    nome: str
    no_ini: int
    no_fim: int
    categoria_via: Optional[CategoriaVia] = None
    posicao: Optional[Posicao] = None
    concelho: Optional[str] = None
    gestao: Optional[Gestao] = None
    condicao_ativo: Optional[bool] = None


class Taludes(EquiviaBase):
    via_auxiliar: ViaAuxiliar
    n_via: Optional[int]
    inclinacao: float
    n_banquetas: int
    largura_banquetas: float
    regueiras_ravinamentos: bool

    @field_validator("regueiras_ravinamentos", "condicao_ativo", mode="before")
    @classmethod
    def booleans(cls, value: int) -> bool:
        return value != 0


class Vedacoes(EquiviaBase):
    via_auxiliar: ViaAuxiliar
    altura: float
    n_portoes: int
    vedacoes: int


EquiviaThings = Union[
    AcessosServentias,
    DrenagemPontual,
    Iluminação,
    IntegracaoPaisagistica,
    MarcoQuilometrico,
    Pavimentos,
    Seccoes,
    Taludes,
    Vedacoes,
]
