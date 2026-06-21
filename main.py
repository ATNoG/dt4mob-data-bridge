import asyncio

from loguru import logger

from devices.device import Device
from interfaces.ipma import populate_stations, populate_warning_areas
from settings import settings
from storage.session import SessionSingleton


async def main():
    await populate_stations()
    await populate_warning_areas()

    logger.info("Loaing the folowing devices: {}", settings.devices)
    devices = [Device.from_settings(d) for d in settings.devices]

    exceptions = await asyncio.gather(
        *[d.run() for d in devices], return_exceptions=True
    )

    for e in exceptions:
        if isinstance(e, BaseException):
            logger.error("An error has occured while running a device. Message: {}", e)

    await SessionSingleton.close_session()


if __name__ == "__main__":
    asyncio.run(main())
