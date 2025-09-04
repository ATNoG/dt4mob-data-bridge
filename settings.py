from enum import Enum
from pydantic import AnyHttpUrl, BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Environment(str, Enum):
    PROD = "prod"
    DEV = "dev"


class HonoSettings(BaseModel):
    """Settings for establishing a connection with the Hono Instance"""

    device_registry: AnyHttpUrl = AnyHttpUrl("http://localhost:28443")
    http_adapter: AnyHttpUrl = AnyHttpUrl("http://localhost:8443")
    tenant_id: str = "DEFAULT_TENANT"
    device_id: str = ""
    passwd: str = "secret"
    policy_id: str = ""


class Settings(BaseSettings):
    """Example loading values from the table used by default."""

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )

    hono: HonoSettings = HonoSettings()
    env: Environment = Environment.PROD

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
