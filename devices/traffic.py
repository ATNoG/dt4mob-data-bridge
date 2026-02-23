from typing import Any

from devices.ditto import Device
from interfaces.hono import HonoDevice
from models.ditto import Feature
from models.waze import WazeRequest
from storage.station import StationSingleton
from settings import Toll


class TrafficDevice(Device):
    def __init__(self, hono_conn: HonoDevice) -> None:
        super().__init__(hono_conn)

    async def modify(self, device: Any, data: Any) -> None:
        assert isinstance(device, Toll)
        assert isinstance(data, WazeRequest)
        attributes = {
            "location": {"latitude": device.latitude, "longitude": device.longitude},
            "name": device.name,
        }

        features = {"traffic": Feature(properties=data.model_dump())}
        message = self.modify_message(
            device.name, attributes=attributes, features=features
        )

        await self._hono.send_telemetry(message)
