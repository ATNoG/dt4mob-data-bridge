import asyncio

from loguru import logger

from devices.device import Device
from settings import settings


async def main():
    logger.debug("These devices exist: {}", settings.devices)
    devices = [Device.from_settings(d) for d in settings.devices]

    logger.debug("devices contains {}", devices)

    for device in devices:
        logger.debug(
            "This device exists: {},{},{}",
            device.cert_path,
            device.secret_key,
            device.strategies,
        )
        await device.run()


if __name__ == "__main__":
    asyncio.run(main())
