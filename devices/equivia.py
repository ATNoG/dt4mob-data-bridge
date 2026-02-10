from devices.ditto import Device
from interfaces.hono import HonoDevice
from models.equivia import EquiviaThings



class EquiviaDevice(Device):
    def __init__(self, hono_dev: HonoDevice):
        super().__init__(hono_dev)

    async def modify(self, device: None, data: EquiviaThings) -> None:
        message = self.modify_message(
            f"{data.type}-{data.object_id}", attributes=data.model_dump()
        )

        await self._hono.send_telemetry(message)
        # logger.info("MOCK - Sending Message {}", message)
