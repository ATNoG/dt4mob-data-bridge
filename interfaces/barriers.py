import json
from loguru import logger
from pyproj.transformer import Transformer
from typing import List
from models.geo import Point
from models.barriers import Barrier
from settings import settings

transformer = Transformer.from_crs("EPSG:3763", "EPSG:4326")


def generate_barrier(js: dict):
    for feature in js.get("features", []):
        barrier = feature.get("properties", {})
        line: List[List[int]] = feature.get("geometry", []).get("coordinates", [])[0]
        barrier["geometry"] = [convert_coordinates(coords) for coords in line]
        yield Barrier(**barrier)


def convert_coordinates(coords: list[int]) -> Point:
    # create transformer from ETRS89 / Portugal TM06 to WGS84 lon/lat

    assert len(coords) == 2  # Ensure that there are 2 coordinates
    new_coords = transformer.transform(coords[0], coords[1])
    return Point(x=new_coords[1], y=new_coords[0])


def get_barrier() -> List[Barrier]:
    file = settings.barriers.dir
    ret: List[Barrier] = []

    logger.info("The barriers' file is in {}", file)
    with open(file, "r") as f:
        try:
            jason = json.loads(f.read())
        except Exception as e:
            logger.error("An error has occured while loading the GeoJSON in {}", file)
            raise RuntimeError(e)

    logger.debug("GeoGSON loaded with success")
    ret.extend(generate_barrier(jason))

    logger.debug("Got a total of {} barriers", len(ret))
    return ret
