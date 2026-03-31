import os
import json
from typing import Any, Generator, List
from loguru import logger
from pyproj.transformer import Transformer
from models.signs import Sign
from models.geo import Point
from settings import settings
from utils.geo import get_geotile

transformer = Transformer.from_crs("EPSG:3763", "EPSG:4326")


def read_files(dir: str) -> Generator[str, None, None]:
    logger.info("Reading directory {}", dir)
    files = os.listdir(dir)

    for file in files:
        logger.debug("Attempting to load the Sign GeoJSON data in {}", file)
        with open(f"{dir}/{file}", "r") as f:
            yield f.read()


def generate_signs(js: dict[str, Any]) -> Generator[Sign, None, None]:
    sign_type = js.get("name")
    for feature in js.get("features", []):
        sign = feature.get("properties", {})
        coords: List[int] = feature.get("geometry", {}).get("coordinates", [])
        sign["type"] = sign_type
        location = convert_coordinates(coords)
        sign["location"] = location
        sign["geotile"] = get_geotile(location.latitude, location.longitude, 31)
        yield Sign(**sign)


def convert_coordinates(coords: list[int]) -> Point:
    # create transformer from ETRS89 / Portugal TM06 to WGS84 lon/lat

    assert len(coords) == 2  # Ensure that there are 2 coordinates
    new_coords = transformer.transform(coords[0], coords[1])
    return Point(x=new_coords[1], y=new_coords[0])


def get_signs() -> List[Sign]:
    dir = settings.signs.dir
    ret: List[Sign] = []

    for file in read_files(dir):
        try:
            jason = json.loads(file)
        except Exception as e:
            logger.error("An error has occured while loading the GeoJSON in {}", file)
            raise RuntimeError(e)

        logger.debug("GeoGSON loaded with success")
        ret.extend(generate_signs(jason))

    logger.debug("Got a total of {} signs", len(ret))
    return ret
