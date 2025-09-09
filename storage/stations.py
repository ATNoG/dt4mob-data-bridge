import asyncio
from typing import List, Set
from geopy import Point
from geopy.distance import geodesic
from loguru import logger
from models.stations import Station


class StationSingleton:
    _stations: Set[Station]
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def set_stations(cls, stations: List[Station]):
        async with cls._lock:
            cls._stations = set(stations)

    @classmethod
    def get_stations(cls):
        return cls._stations

    @classmethod
    def get_closest_stations(cls, latitude: float, longitude: float) -> List[Station]:
        logger.debug("Getting the closest stations to ({},{})", latitude, longitude)
        poi = Point(latitude, longitude)
        coords = (
            (Point(d.latitude, d.longitude), d) for i, d in enumerate(cls._stations)
        )

        closest = sorted((geodesic(p, poi).km, i) for p, i in coords)[:3]
        logger.debug("The closest stations are {}", closest)

        return [i for _, i in closest]
