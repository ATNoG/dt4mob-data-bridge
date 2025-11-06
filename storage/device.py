from typing import Optional

from devices.ditto import Device
from devices.meteo import MeteoDevice
from devices.traffic import TrafficDevice
from devices.signs import SignDevice
from interfaces.hono import HonoDevice
from settings import DeviceSettings, DeviceType
from storage.session import SessionSingleton


class DevicesSingleton:
    devices: dict[DeviceType, Device] = {}

    @classmethod
    def get_device(cls, device_type: DeviceType) -> Optional[Device]:
        return cls.devices.get(device_type)

    @classmethod
    def add_device(cls, device: DeviceSettings) -> HonoDevice:
        item = None

        hono_conn = HonoDevice(
            SessionSingleton.get_session(),
            device.type.value,
            device.passwd,
            device.policy_id,
        )

        match device.type:
            case DeviceType.METEO:
                item = MeteoDevice(hono_conn)

            case DeviceType.TRAFFIC:
                item = TrafficDevice(hono_conn)

            case DeviceType.SIGN:
                item = SignDevice(hono_conn)

        cls.devices[device.type] = item
        return hono_conn
