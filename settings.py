from typing import List, Optional, Self

from pydantic import AnyHttpUrl, BaseModel, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from strategies import StrategyType


class HonoSettings(BaseModel):
    """Settings for establishing a connection with the Hono Instance"""

    http_adapter: AnyHttpUrl = AnyHttpUrl("http://localhost:8443")
    tenant_id: str = "DEFAULT_TENANT"
    server_cert_path: Optional[str] = None


class DeviceSettings(BaseModel):
    policy_id: str
    # HACK: The namespace is configured by the certificate (?) but needs to go
    # on the topic, hence it also needing to be on the settings
    # TODO: See if this namespace can be derived at runtime from the certificate
    namespace: str
    cert_path: str
    private_key: str
    strategies: List[StrategyType]

    @model_validator(mode="after")
    def validate_strategies(self) -> Self:
        if len(self.strategies) < 1:
            raise ValueError("A device must have atleast 1 strategy")
        return self


class Settings(BaseSettings):
    """Example loading values from the table used by default."""

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )

    hono: HonoSettings = HonoSettings()
    devices: List[DeviceSettings] = []

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
