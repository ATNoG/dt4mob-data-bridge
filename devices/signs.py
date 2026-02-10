
from devices.ditto import Device
from interfaces.hono import HonoDevice
from models.signs import Sign


class SignDevice(Device):
    def __init__(self, hono_dev: HonoDevice):
        super().__init__(hono_dev)

    async def modify(self, device: None, data: Sign) -> None:
        message = self.modify_message(
            f"{data.type}-{str(data.objectID)}", attributes=data.model_dump()
        )

        await self._hono.send_telemetry(message)
