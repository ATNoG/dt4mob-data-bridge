from devices.ditto import Device
from interfaces.hono import HonoDevice
from models.meteo import Measurement, Station
from models.ditto import Feature


class MeteoDevice(Device):
    def __init__(self, hono_dev: HonoDevice):
        super().__init__(hono_dev)

    async def modify(self, device: Station, data: Measurement) -> None:
        features = {"meteorology": Feature(properties=data.model_dump())}
        message = self.modify_message(str(device.id), device.model_dump(), features)
        await self._hono.send_telemetry(message)
