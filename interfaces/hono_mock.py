from loguru import logger
from pydantic import BaseModel

from interfaces.hono import HonoDevice


class MockDevice(HonoDevice):
    def __init__(self, cert_path: str, private_key: str):
        logger.info(
            "MOCK: Creating a mock device with certPath: {} and key: {}",
            cert_path,
            private_key,
        )

    async def send_telemetry(self, message: BaseModel) -> None:
        jason = message.model_dump_json(exclude_none=True)

        logger.info(
            "MOCK: The following message would be sent to Eclipse Hono: {}", jason
        )
