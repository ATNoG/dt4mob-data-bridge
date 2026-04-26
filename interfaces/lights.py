import json
from typing import Any, Generator, List
from loguru import logger

from models.geo import Point
from models.lights import Light
from settings import settings
from utils.geo import get_geotile


def generate_lights(js: dict[str, Any]) -> Generator[Light, None, None]:
    lights_type = js.get("name", "Lights")
    for feature in js.get("features", []):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {})
        props["type"] = lights_type

        geometry_type = coords.get("type", "")
        coordinates = coords.get("coordinates", [])

        if geometry_type == "Point" and len(coordinates) >= 2:
            location = Point(x=coordinates[0], y=coordinates[1])
        else:
            logger.warning("Unsupported geometry type {} for light", geometry_type)
            continue

        props["location"] = location
        props["geotile"] = get_geotile(location.latitude, location.longitude, 31)

        try:
            yield Light(**props)
        except Exception as e:
            logger.debug("The light thing was {}", props)
            logger.error("{}", e)


def get_lights() -> List[Light]:
    file_path = settings.lights.file
    ret: List[Light] = []

    try:
        with open(file_path, "r") as f:
            data = json.loads(f.read())
    except Exception as e:
        logger.error("An error has occured while loading the GeoJSON in {}", file_path)
        raise RuntimeError(e)

    logger.debug("GeoJSON loaded with success")
    ret.extend(generate_lights(data))

    logger.debug("Got a total of {} lights", len(ret))
    return ret
