import asyncio
from typing import Dict, List, Optional, Set

from geopy import Point
from geopy.distance import geodesic
from loguru import logger

from models.meteo import Station, WarningArea


class StationSingleton:
    _stations: Set[Station]
    _lock: asyncio.Lock = asyncio.Lock()
    _warning_areas: Dict[str, WarningArea]

    @classmethod
    async def set_warning_areas(cls, areas: List[WarningArea]):
        async with cls._lock:
            cls._warning_areas = {area.warning_area: area for area in areas}

    @classmethod
    async def get_warning_area(cls, area_id: str) -> Optional[WarningArea]:
        async with cls._lock:
            return cls._warning_areas.get(area_id)

    @classmethod
    async def set_stations(cls, stations: List[Station]) -> None:
        async with cls._lock:
            cls._stations = set(stations)

    @classmethod
    async def get_closest_stations(
        cls, latitude: float, longitude: float, max_distance: float = 100.0
    ) -> List[Station]:
        logger.debug("Getting the closest stations to ({},{})", latitude, longitude)
        poi = Point(latitude, longitude)
        async with cls._lock:
            coords = (
                (Point(d.location.latitude, d.location.longitude), d)
                for d in cls._stations
            )

        closest = sorted((geodesic(p, poi).km, i) for p, i in coords)[:3]
        logger.debug("The closest stations are {}", closest)

        if all(distance > max_distance for distance, _ in closest):
            logger.error(
                "There are no stations nearby\n\t Point: ({},{})\n\t Closest: {}",
                latitude,
                longitude,
                closest,
            )
        return [i for dist, i in closest if dist <= max_distance]
