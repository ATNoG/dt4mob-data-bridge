from devices.ditto import Device
from models.ditto import Feature
from models.waze import WazeRequest
from storage import StationSingleton
from settings import Toll


class TrafficDevice(Device):
    def __init__(self, hono_conn) -> None:
        super().__init__(hono_conn)

    async def modify(self, device: Toll, data: WazeRequest) -> None:
        attributes = {
            "meteo_stations": [
                f"{self.id}:{station.id}"
                for station in StationSingleton.get_closest_stations(
                    device.latitude, device.longitude
                )
            ],
            "latitude": device.latitude,
            "longitude": device.longitude,
            "name": device.name,
        }

        features = {"traffic": Feature(properties=data.model_dump())}
        message = self.modify_message(device.name, attributes, features=features)

        await self._hono.send_telemetry(message)
