import json
from datetime import datetime, timezone
from typing import List, Tuple

from aiohttp import ClientResponseError
from loguru import logger

from session import SessionSingleton
from models.measurements import Measurement
from models.stations import Station


async def get_measurements() -> List[Tuple[Station, Measurement]]:
    """
    Function responsible for getting the existing stations and measurements from IPMA.pt
    This function utilizes IPMA's Open API to get the GeoJSON from the last measurements,
    since this is the only endpoint with Station information
    """
    session = SessionSingleton.get_session()
    logger.info("Querying IPMA for new measurements")
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
        measurement_datetime = datetime.strptime(
            d["properties"]["time"], "%Y-%m-%dT%H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        if (current_time - measurement_datetime).total_seconds() > 3600:
            continue

        if d["properties"]["idDireccVento"] == 9:
            d["properties"]["idDireccVento"] = 0
        res.append(
            (
                Station(
                    id=d["properties"]["idEstacao"],
                    latitude=d["geometry"]["coordinates"][1],
                    longitude=d["geometry"]["coordinates"][0],
                    location=d["properties"]["localEstacao"],
                ),
                Measurement(**d["properties"]),
            )
        )

    if not res:
        logger.error("No new measurements were found on IPMA.pt")
        raise RuntimeError("No Measurements found on IPMA")

    logger.debug("Measurements acquired successfully")

    return res
