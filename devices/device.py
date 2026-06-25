from typing import List

from loguru import logger

from interfaces.hono import HonoDevice
from settings import DeviceSettings
from strategies import acquire_strategies
from strategies.strategy import BaseStrategy
from utils.batch import batch_cooldown


class Device:
    cert_path: str
    private_key: str
    strategies: List[BaseStrategy]

    def __init__(
        self, cert_path: str, private_key: str, strategies: List[BaseStrategy]
    ):
        self.cert_path = cert_path
        self.private_key = private_key
        self.strategies = strategies
        self.hono_conn = HonoDevice(cert_path, private_key)

    @classmethod
    def from_settings(cls, settings: DeviceSettings) -> "Device":
        return Device(
            cert_path=settings.cert_path,
            private_key=settings.private_key,
            strategies=acquire_strategies(
                settings.strategies, settings.policy_id, settings.namespace
            ),
        )

    async def run(self) -> None:
        try:
            for strategy in self.strategies:
                messages = await strategy.get_telemetry()

                for i, message in enumerate(messages):
                    try:
                        await self.hono_conn.send_telemetry(message)
                    except Exception as e:
                        logger.error(
                            "An exception has occured while running a device with cert: {}. Message: {}",
                            self.cert_path,
                            e,
                        )
                    await batch_cooldown(i)

        finally:
            await self.hono_conn.close_session()
