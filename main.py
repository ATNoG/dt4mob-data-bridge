import asyncio

from devices.device import Device
from settings import settings


async def main():
    devices = [Device.from_settings(d) for d in settings.devices]

    for device in devices:
        await device.run()


if __name__ == "__main__":
    asyncio.run(main())
