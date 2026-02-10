from math import cos

from loguru import logger
from pydantic import BaseModel

from models.waze import WazeRequest
from storage.session import SessionSingleton


class _Limits(BaseModel):
    top: float
    bottom: float
    left: float
    right: float


def _get_limits(radius: float, lat: float, lon: float) -> _Limits:
    """
    The Waze API receives a rectangular area and returns all the jams and alerts that
    are contained within that area. To get the area from the center point and the radius, we need
    to calculate 4 points, and return the corresponding latitude and longitude of the limits.
    """
    radius = radius / 1000
    radiusLon = 1 / (111.319 * cos(lat)) * radius
    radiusLat = 1 / 110.574 * radius * (1 if lon >= 0 else -1)

    return _Limits(
        top=lat + radiusLat,
        bottom=lat - radiusLat,
        left=lon - radiusLon,
        right=lon + radiusLon,
    )


async def get_traffic_data(lat: float, lon: float, radius: float):
    session = SessionSingleton.get_session()
    lim = _get_limits(radius, lat, lon)
    url = f"https://www.waze.com/live-map/api/georss?top={lim.top}&bottom={lim.bottom}&left={lim.left}&right={lim.right}&env=row&types=traffic,alerts"
    logger.info("Getting Alerts and Jams for ({},{})", lat, lon)
    logger.debug("The url is: {}", url)
    data = await session.get(url)
    return WazeRequest(**(await data.json()))
