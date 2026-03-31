import os
import json
from typing import Any, Generator, List
from loguru import logger
from pyproj.transformer import Transformer

from models.geo import Point, PolyLine
from settings import settings
from utils.geo import get_geotile
from models.equivia import (
    AcessosServentias,
    DrenagemPontual,
    IntegracaoPaisagistica,
    MarcoQuilometrico,
    Pavimentos,
    Seccoes,
    Taludes,
    Vedacoes,
    Iluminação,
    EquiviaThings,
)

transformer = Transformer.from_crs("EPSG:3763", "EPSG:4326")


def read_files(dir: str) -> Generator[str, None, None]:
    logger.info("Reading directory {}", dir)
    files = os.listdir(dir)

    for file in files:
        logger.debug("Attempting to load the Equivia GeoJSON data in {}", file)

        with open(f"{dir}/{file}", "r") as f:
            yield f.read()


def convert_coordinates(coords: list[int]) -> Point:
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


def generate_things(js: dict[str, Any]) -> Generator[EquiviaThings, None, None]:
    equivia_type = js.get("name")
    for feature in js.get("features", []):
        thing = feature.get("properties", {})
        coords = feature.get("geometry", [])
        thing["type"] = equivia_type
        if coords.get("type", "") == "Point":
            thing["location"] = convert_coordinates(coords.get("coordinates"))
        elif coords.get("type", "") == "MultiLineString":
            thing["location"] = PolyLine(
                [convert_coordinates(x) for x in coords.get("coordinates")[0]]
            )
        else:
            thing["location"] = PolyLine(
                [convert_coordinates(x) for x in coords.get("coordinates")[0][0]]
            )

        segments: list[Point] | list[PolyLine]
        if isinstance(thing["location"], Point):
            segments = [thing["location"]]
        else:
            assert isinstance(thing["location"], PolyLine)
            segments = thing["location"].split_line()

        objid = thing["OBJECTID"]
        for i, v in enumerate(segments):
            if len(segments) > 1:
                thing["OBJECTID"] = f"{objid}-{i}"
                thing["location"] = v

            # Use the first point of the location to calculate the geotile
            location_point: Point
            if isinstance(thing["location"], Point):
                location_point = thing["location"]
            else:
                assert isinstance(thing["location"], PolyLine)
                location_point = thing["location"].root[0]

            thing["geotile"] = get_geotile(
                location_point.latitude, location_point.longitude, 31
            )

            try:
                match equivia_type:
                    case "AcessosServentias":
                        yield AcessosServentias(**thing)
                    case "DrenagemPontual":
                        yield DrenagemPontual(**thing)
                    case "Iluminacao":
                        yield Iluminação(**thing)
                    case "IntegracaoPaisagistica":
                        yield IntegracaoPaisagistica(**thing)
                    case "MarcosQuilometricos":
                        yield MarcoQuilometrico(**thing)
                    case "Pavimentos":
                        yield Pavimentos(**thing)
                    case "Seccoes":
                        yield Seccoes(**thing)
                    case "Taludes":
                        yield Taludes(**thing)
                    case "Vedacoes":
                        yield Vedacoes(**thing)
            except Exception as e:
                logger.debug("The thing was {}", thing)
                logger.error("{}", e)


def get_equivia() -> List[EquiviaThings]:
    dir = settings.equivia.dir
    ret: List[EquiviaThings] = []

    for file in read_files(dir):
        try:
            jason = json.loads(file)
        except Exception as e:
            logger.error("An error has occured while loading the GeoJSON in {}", file)
            raise RuntimeError(e)

        logger.debug("GeoGSON loaded with success")
        ret.extend(generate_things(jason))

    logger.debug("Got a total of {} road features", len(ret))
    return ret
