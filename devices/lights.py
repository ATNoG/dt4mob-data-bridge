from devices.ditto import Device
from interfaces.hono import HonoDevice
from models.lights import Light


class LightsDevice(Device):
    def __init__(self, hono_dev: HonoDevice):
        super().__init__(hono_dev)

    async def modify(self, device: None, data: Light) -> None:
        message = self.modify_message(
            f"{data.type}-{str(data.object_id)}", attributes=data.model_dump()
        )

        await self._hono.send_telemetry(message)
