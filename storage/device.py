from typing import Optional

from devices.ditto import Device
from devices.meteo import MeteoDevice
from devices.traffic import TrafficDevice
from devices.signs import SignDevice
from devices.barriers import BarrierDevice
from devices.equivia import EquiviaDevice
from devices.lights import LightsDevice
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
        item: Device

        # Pass the appropriate authentication method based on what's configured
        # The validator ensures exactly one of passwd or cert_path is set
        hono_conn = HonoDevice(
            SessionSingleton.get_session(),
            device.type.value,
            device.policy_id,
            device.passwd,
            device.cert_path,
        )

        match device.type:
            case DeviceType.METEO:
                item = MeteoDevice(hono_conn)

            case DeviceType.TRAFFIC:
                item = TrafficDevice(hono_conn)

            case DeviceType.SIGN:
                item = SignDevice(hono_conn)

            case DeviceType.BARRIER:
                item = BarrierDevice(hono_conn)

            case DeviceType.EQUIVIA:
                item = EquiviaDevice(hono_conn)

            case DeviceType.LIGHTS:
                item = LightsDevice(hono_conn)

        cls.devices[device.type] = item
        return hono_conn
