from enum import Enum
from typing import Optional
from pydantic import Field, BaseModel
from models.geo import Point


class Estado(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    COLOCADO = "1"
    RETIRADO = "2"
    SUBSTITUIDO = "3"

    def __str__(self):
        match self:
            case self.COLOCADO:
                return "Colocado"
            case self.RETIRADO:
                return "Retirado"
            case self.SUBSTITUIDO:
                return "Substituído"


class Sentidoleitura(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    CRESCENTE = "1"
    DECRESCENTE = "2"

    def __str__(self):
        match self:
            case self.CRESCENTE:
                return "Crescente"
            case self.DECRESCENTE:
                return "Decrescente"


class TipoAmbRod(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    PLENA_VIA_PV = "1"
    RAMO_DE_NO_DE_LIGACAO = "2"
    LIG_DIR_ENTRADA_NA_PV = "3"
    LIG_DIR_SAIDA_DA_PV = "4"
    LIG_ESQ_ENTRADA_NA_PV = "5"
    LIG_ESQ_SAIDA_DA_PV = "6"

    def __str__(self):
        match self:
            case self.PLENA_VIA_PV:
                return "Plena via (PV)"
            case self.RAMO_DE_NO_DE_LIGACAO:
                return "Ramo de nó de ligação"
            case self.LIG_DIR_ENTRADA_NA_PV:
                return "Lig. à dir. - Entrada na PV"
            case self.LIG_DIR_SAIDA_DA_PV:
                return "Lig. à dir. - Saída da PV"
            case self.LIG_ESQ_ENTRADA_NA_PV:
                return "Lig. à esq. - Entrada na PV"
            case self.LIG_ESQ_SAIDA_DA_PV:
                return "Lig. à esq. - Saída da PV"


class Posicao(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    BERMA_ESQUERDA = "2"
    SOBRE_VIA_RAMO_LIGACAO = "3"
    ILHEU_SEPARADOR_CENTRAL = "4"
    ILHA_CENTRAL_ROTUNDA = "5"
    LOCAL_DE_DIVERGENCIA = "6"
    BERMA_DIREITA = "1"

    def __str__(self):
        match self:
            case self.BERMA_ESQUERDA:
                return "Berma esquerda"
            case self.SOBRE_VIA_RAMO_LIGACAO:
                return "Sobre a via/ ramo/ ligação"
            case self.ILHEU_SEPARADOR_CENTRAL:
                return "Ilheu/ separador central"
            case self.ILHA_CENTRAL_ROTUNDA:
                return "Ilha central (rotunda)"
            case self.LOCAL_DE_DIVERGENCIA:
                return "Local de divergência"
            case self.BERMA_DIREITA:
                return "Berma direita"


class Classeretroface(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    RA1 = "1"
    RA2 = "2"
    RA3 = "3"

    def __str__(self):
        match self:
            case self.RA1:
                return "RA1"
            case self.RA2:
                return "RA2"
            case self.RA3:
                return "RA3"


class Substrato(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    ALUMINIO = "1"
    FERRO_GALVANIZADO = "2"
    FIBRA_DE_VIDRO = "3"
    PVC = "4"
    BETAO = "5"
    PEDRA = "6"
    MADEIRA = "7"

    def __str__(self):
        match self:
            case self.ALUMINIO:
                return "Alumínio"
            case self.FERRO_GALVANIZADO:
                return "Ferro galvanizado"
            case self.FIBRA_DE_VIDRO:
                return "Fibra de vidro"
            case self.PVC:
                return "PVC"
            case self.BETAO:
                return "Betão"
            case self.PEDRA:
                return "Pedra"
            case self.MADEIRA:
                return "Madeira"


class Fabricantes(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    BRICANTEL = "1"
    FL_GASPAR = "2"
    INTERVEGA = "3"
    ISIDOVIAS = "4"
    MASITRAVE = "5"
    MEIO_CORTE = "6"
    PEGADO = "7"
    NADIA = "8"
    SINALARTE = "9"
    SNSV = "10"
    TRAFIURBE = "11"
    VIAMARCA = "12"
    OUTRO_FABRICANTE_OBSER = "13"
    TRACEVIA = "14"
    MONSEGUR = "15"
    PRIETO = "16"
    SINAT = "17"
    SINALNORTE = "18"
    LUSOESTRADA = "19"
    SOPRESTIGIO = "20"
    SERLIX = "21"
    ROADSIGN = "22"

    def __str__(self):
        match self:
            case self.BRICANTEL:
                return "BRICANTEL"
            case self.FL_GASPAR:
                return "FL GASPAR"
            case self.INTERVEGA:
                return "INTERVEGA"
            case self.ISIDOVIAS:
                return "ISIDOVIAS"
            case self.MASITRAVE:
                return "MASITRAVE"
            case self.MEIO_CORTE:
                return "MEIO CORTE"
            case self.PEGADO:
                return "PEGADO"
            case self.NADIA:
                return "NADIA"
            case self.SINALARTE:
                return "SINALARTE"
            case self.SNSV:
                return "SNSV"
            case self.TRAFIURBE:
                return "TRAFIURBE"
            case self.VIAMARCA:
                return "VIAMARCA"
            case self.OUTRO_FABRICANTE_OBSER:
                return "Outro Fabricante (Obser.)"
            case self.TRACEVIA:
                return "TRACEVIA"
            case self.MONSEGUR:
                return "MONSEGUR"
            case self.PRIETO:
                return "PRIETO"
            case self.SINAT:
                return "SINAT"
            case self.SINALNORTE:
                return "SINALNORTE"
            case self.LUSOESTRADA:
                return "LUSOESTRADA"
            case self.SOPRESTIGIO:
                return "SOPRESTIGIO"
            case self.SERLIX:
                return "SERLIX"
            case self.ROADSIGN:
                return "ROADSIGN"


class Faced(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    NORTE = "1"
    SUL = "2"
    ESTE = "3"
    OESTE = "4"
    NORDESTE = "5"
    SUDESTE = "6"
    SUDOESTE = "7"
    NOROESTE = "8"

    def __str__(self):
        match self:
            case self.NORTE:
                return "Norte"
            case self.SUL:
                return "Sul"
            case self.ESTE:
                return "Este"
            case self.OESTE:
                return "Oeste"
            case self.NORDESTE:
                return "Nordeste"
            case self.SUDESTE:
                return "Sudeste"
            case self.SUDOESTE:
                return "Sudoeste"
            case self.NOROESTE:
                return "Noroeste"


class Motsubst(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    ACIDENTE = "1"
    DESGASTE = "2"
    FOGO = "3"
    FURTO = "4"
    SS_SGR = "5"
    VANDALISMO = "6"
    NAO_APLICAVEL = "7"

    def __str__(self):
        match self:
            case self.ACIDENTE:
                return "Acidente"
            case self.DESGASTE:
                return "Desgaste"
            case self.FOGO:
                return "Fogo"
            case self.FURTO:
                return "Furto"
            case self.SS_SGR:
                return "SS-SGR"
            case self.VANDALISMO:
                return "Vandalismo"
            case self.NAO_APLICAVEL:
                return "Não Aplicável"


class Gestao(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    IP = "0"
    SUBCONCESSAO = "1"
    CONCESSAO = "2"
    MUNICIPIO = "3"

    def __str__(self):
        match self:
            case self.IP:
                return "IP"
            case self.SUBCONCESSAO:
                return "Subconcessao"
            case self.CONCESSAO:
                return "Concessao"
            case self.MUNICIPIO:
                return "Municipio"


class Ec(str, Enum):
    """
    IPGIS_SINAL_2018
    """

    EC1 = "1"
    EC2 = "2"
    EC3 = "3"

    def __str__(self):
        match self:
            case self.EC1:
                return "EC1"
            case self.EC2:
                return "EC2"
            case self.EC3:
                return "EC3"


class Forma(str, Enum):
    TRIANGULO_EQUILATERO_0 = "0"
    TRIANGULO_EQUILATERO_1 = "1"
    CIRCULAR = "2"
    QUADRADA = "3"
    RETANGULAR_4 = "4"
    OCTOGONO_REGULAR = "5"
    RETANGULAR_6 = "6"
    SETA = "7"
    OUTRA = "8"

    def __str__(self):
        match self:
            case self.TRIANGULO_EQUILATERO_0:
                return "Triângulo equilátero"
            case self.TRIANGULO_EQUILATERO_1:
                return "Triângulo equilátero"
            case self.CIRCULAR:
                return "Circular"
            case self.QUADRADA:
                return "Quadrada"
            case self.RETANGULAR_4:
                return "Retangular"
            case self.RETANGULAR_6:
                return "Retangular"
            case self.OCTOGONO_REGULAR:
                return "Octógono regular"
            case self.SETA:
                return "Seta"
            case self.OUTRA:
                return "Outra"


class Sign(BaseModel):
    type: str
    objectID: int = Field(alias="OBJECTID")
    codRST: int = Field(alias="codrst")
    formaSinal: Forma = Field(alias="formsinal")
    estado: Estado
    codipsinal: int
    via: Optional[str]
    sentidoVia: Sentidoleitura = Field(alias="sentidoviaip")
    tipoAmbRod: TipoAmbRod = Field(alias="tipoambrod")
    posicao: Posicao
    classeRetroFace: Classeretroface = Field(alias="classeretroface")
    substrato: Substrato
    altura: float = Field(alias="dimsinalaltura")
    largura: float = Field(alias="dimsinallargura")
    fabricante: Fabricantes = Field(alias="fabricantesinal")
    distrito: str
    faced: Optional[Faced]
    motSubst: Optional[Motsubst] = Field(alias="motsubst")
    gestao: Optional[Gestao]
    ec: Optional[Ec]
    pk: Optional[float]
    location: Point
