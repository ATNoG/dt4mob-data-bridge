from devices.ditto import Device
from interfaces.hono import HonoDevice
from models.barriers import Barrier


class BarrierDevice(Device):
    def __init__(self, hono_dev: HonoDevice):
        super().__init__(hono_dev)

    async def modify(self, device: None, data: Barrier) -> None:
        message = self.modify_message(str(data.objectID), attributes=data.model_dump())

        await self._hono.send_telemetry(message)
