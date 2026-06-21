import asyncio
from typing import List

from loguru import logger

from interfaces.hono_mock import MockDevice
from settings import DeviceSettings
from strategies import acquire_strategies
from strategies.strategy import BaseStrategy


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
        self.hono_conn = MockDevice(cert_path, private_key)

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

                exceptions = await asyncio.gather(
                    *[self.hono_conn.send_telemetry(message) for message in messages],
                    return_exceptions=True,
                )

                for e in exceptions:
                    if isinstance(e, BaseException):
                        logger.error(
                            "An exception has occured while running a device with cert: {}. Message: {}",
                            self.cert_path,
                            e,
                        )

        finally:
            await self.hono_conn.close_session()
