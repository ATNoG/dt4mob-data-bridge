import math

from loguru import logger
from pyproj import Transformer

from models.geo import Point, PolyLine


def get_geotile(lat: float, lng: float, zoom: int) -> int:
    x = int((lng + 180) / 360 * (1 << zoom))
    y = int(
        (
            1
            - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat)))
            / math.pi
        )
        / 2
        * (1 << zoom)
    )

    quadkey = 0
    for i in range(zoom, 0, -1):
        x_bit = (x >> i) & 1
        y_bit = (y >> i) & 1
        quadkey = (quadkey << 2) | (y_bit << 1) | x_bit
    return quadkey


def convert_coordinates(coords: list[int]) -> Point:
    transformer = Transformer.from_crs("EPSG:3763", "EPSG:4326")
    if len(coords) < 2:
        logger.critical("The coordinate list to convert was invalid {}", coords)
        raise RuntimeError("Invalid Coordinates")
    new_coords = transformer.transform(coords[0], coords[1])
    try:
        return Point(x=new_coords[1], y=new_coords[0])
    except Exception as e:
        logger.critical(
            "An error has occured while creating the point (x={},y={}) from coords {}, {}",
            new_coords[1],
            new_coords[0],
            coords,
            e,
        )
        raise e


def representative_point(location: Point | PolyLine | None) -> Point | None:
    """
    Returns a single representative Point. For a list of points , the geometric
    centroid (mean latitude, mean longitude) is returned.
    """
    if location is None:
        return None

    if isinstance(location, Point):
        return location

    if not location:
        return None

    return Point(
        x=sum(p.longitude for p in location) / len(location),
        y=sum(p.latitude for p in location) / len(location),
    )
