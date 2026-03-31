from enum import Enum
from typing import List, Optional, Self

from pydantic import AnyHttpUrl, BaseModel, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Environment(str, Enum):
    PROD = "prod"
    DEV = "dev"


class DeviceType(str, Enum):
    TRAFFIC = "traffic"
    METEO = "meteo"
    SIGN = "sign"
    BARRIER = "barrier"
    EQUIVIA = "equivia"


class HonoSettings(BaseModel):
    """Settings for establishing a connection with the Hono Instance"""

    device_registry: AnyHttpUrl = AnyHttpUrl("http://localhost:28443")
    http_adapter: AnyHttpUrl = AnyHttpUrl("http://localhost:8443")
    tenant_id: str = "DEFAULT_TENANT"
    server_cert_path: Optional[str] = None


class DeviceSettings(BaseModel):
    type: DeviceType = DeviceType.TRAFFIC
    policy_id: str = ""
    passwd: Optional[str] = None
    cert_path: Optional[str] = None

    @model_validator(mode="after")
    def validate_credentials(self) -> Self:
        if (self.passwd is not None) + (self.cert_path is not None) != 1:
            raise ValueError(
                "A device must have one and only one authentication method"
            )
        return self


class Toll(BaseModel):
    name: str
    road: str
    latitude: float
    longitude: float
    area_radius: int = 1000


class SignData(BaseModel):
    dir: str = ""


class BarrierData(BaseModel):
    dir: str = ""


class EquiviaData(BaseModel):
    dir: str = ""


class Settings(BaseSettings):
    """Example loading values from the table used by default."""

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )

    hono: HonoSettings = HonoSettings()
    env: Environment = Environment.PROD
    polling_interval: int = 3600
    tolls: List[Toll] = []
    devices: List[DeviceSettings] = []
    signs: SignData = SignData()
    barriers: BarrierData = BarrierData()
    equivia: EquiviaData = EquiviaData()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            env_settings,
            TomlConfigSettingsSource(settings_cls),
        )


settings = Settings()
