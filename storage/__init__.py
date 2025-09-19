from typing import Optional
from aiohttp import ClientSession

import asyncio
from typing import List, Set
from geopy import Point
from geopy.distance import geodesic
from loguru import logger
from models.meteo import Station

from devices.ditto import Device


class DevicesSingleton:
    devices: dict[str, Device] = {}

    @classmethod
    def get_device(cls, device_id: str) -> Optional[Device]:
        return cls.devices.get(device_id)

    @classmethod
    def add_device(cls, device: Device) -> None:
        cls.devices[device.id] = device


class SessionSingleton:
    client: Optional[ClientSession] = None

    @classmethod
    def get_session(cls) -> ClientSession:
        if cls.client is None:
            cls.client = ClientSession()

        return cls.client

    @classmethod
    async def close_session(cls):
        if cls.client:
            await cls.client.close()
            cls.client = None


class StationSingleton:
    _stations: Set[Station]
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def set_stations(cls, stations: List[Station]):
        async with cls._lock:
            cls._stations = set(stations)

    @classmethod
    def get_closest_stations(cls, latitude: float, longitude: float) -> List[Station]:
        logger.debug("Getting the closest stations to ({},{})", latitude, longitude)
        poi = Point(latitude, longitude)
        coords = ((Point(d.latitude, d.longitude), d) for d in cls._stations)

        closest = sorted((geodesic(p, poi).km, i) for p, i in coords)[:3]
        logger.debug("The closest stations are {}", closest)

        return [i for _, i in closest]
