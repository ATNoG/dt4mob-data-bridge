import json
import os
from typing import Any, Generator, List, final

from loguru import logger
from pydantic import ValidationError

from models.ditto import DittoProtocolEnvelope
from models.geo import PolyLine
from models.geojson import GeoJSON
from strategies.strategy import BaseStrategy
from utils.geo import convert_coordinates, get_geotile, representative_point


@final
class GeoJsonStrategy(BaseStrategy):
    def __init__(self, subject: str, policyId: str, dir: str | None, file: str | None):
        super().__init__(subject, policyId)
        if (dir is None) == (file is None):
            raise ValueError(
                "The GeoJSON strategy can only parse either a 'dir' or a 'file', and one must exist. dir: {}; file: {}",
                dir,
                file,
            )

        self.dir = dir
        self.file = file

    async def get_telemetry(self) -> List[DittoProtocolEnvelope]:
        if self.file:
            file = read_file(self.file)
            return self.envelope_from_geojson(file)

        if self.dir:
            return [
                envelope
                for file in read_dir(self.dir)
                for envelope in self.envelope_from_geojson(file)
            ]

        return []

    def envelope_from_geojson(self, jason: GeoJSON) -> List[DittoProtocolEnvelope]:
        features = jason.features

        envelopes = []
        for feature in features:
            attributes = feature.properties
            coords = feature.geometry

            if coords.type == "Point":
                attributes["location"] = convert_coordinates(coords.coordinates)
            elif coords.type == "MultiLineString":
                attributes["location"] = PolyLine(
                    [convert_coordinates(x) for x in coords.coordinates[0]]
                )
            else:
                attributes["location"] = PolyLine(
                    [convert_coordinates(x) for x in coords.coordinates[0][0]]
                )

            midpoint = representative_point(attributes["location"])
            if midpoint:
                geotile = get_geotile(midpoint.latitude, midpoint.longitude, 31)
                attributes["geotile"] = geotile

            id_key = next((key for key in attributes if "ID" in key), "")
            thing_id = attributes.get(id_key, None)

            topic = self._create_topic(str(thing_id))
            envelope = self._create_envelope(topic, attributes)
            envelopes.append(envelope)

        return envelopes


def read_dir(dir: str) -> Generator[Any, None, None]:
    logger.info("Reading directory {}", dir)
    files = os.listdir(dir)

    for file in files:
        logger.debug("Attempting to load the Equivia GeoJSON data in {}", file)

        with open(f"{dir}/{file}", "r") as f:
            try:
                yield read_file(f.read())
            except FileReadError as e:
                logger.error(
                    "Could not get data from file {}, the error was {}", file, e
                )
                pass


def read_file(path: str) -> GeoJSON:
    try:
        ret = json.loads(path)
        return GeoJSON.model_validate(ret)
    except ValidationError:
        logger.error("The file {} does not contain valid GeoJSON")
        raise FileReadError()
    except Exception as e:
        logger.error("An error has occured while loading the GeoJSON in {}", path)
        raise FileReadError(e)


class FileReadError(RuntimeError):
    pass


def _flatten(nested):
    stack = list(nested)
    result = []
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            stack.extend(item)
        else:
            result.append(item)
    return result[::-1]
