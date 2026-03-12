import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from aiohttp import ClientResponseError
from loguru import logger
from pydantic import ValidationError

from models.geo import Point
from models.meteo import Measurement, Station, Warning
from storage.session import SessionSingleton
from storage.station import StationSingleton
from utils.geo import get_quadkey_int, get_quadkey_str


async def get_meteorology_measurements() -> List[Tuple[Station, Measurement]]:
    """
    Function responsible for getting the existing stations and measurements from IPMA.pt
    This function utilizes IPMA's Open API to get the GeoJSON from the last measurements,
    since this is the only endpoint with Station information
    """
    session = SessionSingleton.get_session()
    logger.debug("Querying IPMA for new measurements")
    geojson = await session.get(
        "https://api.ipma.pt/open-data/observation/meteorology/stations/obs-surface.geojson"
    )
    try:
        geojson.raise_for_status()
    except ClientResponseError as e:
        logger.error(
            "An error has occured while getting new measurements from IPMA: {}",
            e.message,
        )
        raise RuntimeError("Could not get measurements from IPMA")

    data = json.loads(await geojson.text())["features"]
    current_time = datetime.now(timezone.utc)

    res = []
    for d in data:
        properties = d["properties"]
        measurement_datetime = datetime.strptime(
            properties["time"], "%Y-%m-%dT%H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        if (current_time - measurement_datetime).total_seconds() > 7200:
            continue

        if properties["idDireccVento"] == 9:
            properties["idDireccVento"] = 0
        point = Point(
            x=d["geometry"]["coordinates"][0], y=d["geometry"]["coordinates"][1]
        )
        station_id = properties["idEstacao"]
        res.append(
            (
                Station(
                    id=station_id,
                    location=point,
                    location_name=d["properties"]["localEstacao"],
                    geohash_int=get_quadkey_int(point.latitude, point.longitude, 31),
                    geohash_str=get_quadkey_str(point.latitude, point.longitude, 31),
                ),
                Measurement(**properties),
            )
        )

    if not res:
        logger.error("No new measurements were found on IPMA.pt")
        raise RuntimeError("No Measurements found on IPMA")

    logger.debug("Measurements acquired successfully")

    return res


async def get_meteorology_warnings() -> Dict[Station, List[Warning]]:
    session = SessionSingleton.get_session()
    logger.debug("Querying IPMA for new meteorologic warnings")
    response = await session.get(
        "https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json"
    )

    try:
        response.raise_for_status()
    except ClientResponseError as e:
        logger.error(
            "An error has occured while querying for the meteorologic warnings: {}",
            e.message,
        )

        return {}

    data = await response.json()
    ret = {}
    now = datetime.now(timezone.utc)
    try:
        warnings = [
            Warning.model_validate(warning_data)
            for warning_data in data
            if warning_data["awarenessLevelID"] not in ("gray", "green")
        ]

        for warning in warnings:
            logger.debug(
                "The warning's end time is {}. Now is {}", warning.end_time, now
            )
            if warning.end_time < now:
                logger.debug("Skipping expired warning: {}", warning)
                continue

            area = await StationSingleton.get_warning_area(warning.warning_area)
            if area is None:
                logger.error("warning: {} - unknown area: {}", warning, area)
                warning.warning_area = "Madeira"
                continue

            warning.warning_area = area.region_name
            closest_stations = await StationSingleton.get_closest_stations(
                area.latitude, area.longitude
            )

            for station in closest_stations:
                stored = ret.get(station, [])
                stored.append(warning)
                ret[station] = stored

    except ValidationError as e:
        logger.warning("Failed to parse warning: {}", e)

    return ret
