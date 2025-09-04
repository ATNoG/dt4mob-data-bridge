import asyncio
from datetime import datetime, timezone
import json
from loguru import logger
from hashlib import sha512
from models.stations import Measurement, Station
from typing import List, Tuple
from aiohttp import BasicAuth, ClientResponseError, ClientSession
from settings import settings, Environment


async def create_hono_device(session: ClientSession):
    logger.debug("Creating device in Hono")
    # If the device exists in the registry, there is no need to create one
    try:
        url = f"{settings.hono.device_registry}v1/devices/{settings.hono.tenant_id}/{settings.hono.device_id}"
        logger.debug("The url is {}", url)
        req = await session.post(
            url,
            ssl=settings.env == Environment.PROD,
        )
        req.raise_for_status()
    except ClientResponseError as e:
        if e.status != 409:
            logger.error("An error occured while creating the device: {}", e.message)
            raise RuntimeError("The device could not be created")

    try:
        await session.put(
            url=f"{settings.hono.device_registry}v1/credentials/{settings.hono.tenant_id}/{settings.hono.device_id}",
            headers={"content-type": "application/json"},
            json=[
                {
                    "type": "hashed-password",
                    "auth-id": f"{settings.hono.device_id}",
                    "secrets": [{"pwd-plain": settings.hono.passwd}],
                }
            ],
            ssl=settings.env == Environment.PROD,
        )
    except ClientResponseError as e:
        logger.error(
            "An error occured while creating the device's credentials: {}", e.message
        )

        await session.delete(
            f"{settings.hono.device_registry}v1/devices/{settings.hono.tenant_id}/{settings.hono.device_id}",
            ssl=settings.env == Environment.PROD,
        )

        raise RuntimeError("The device's credentials could not be created")
    pass


async def get_measurements(session: ClientSession) -> List[Tuple[Station, Measurement]]:
    """
    Function responsible for getting the existing stations and measurements from IPMA.pt
    This function utilizes IPMA's Open API to get the GeoJSON from the last measurements,
    since this is the only endpoint with Station information
    """
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
        if (measurement_datetime - current_time).total_seconds() > 4000:
            continue

        if d["properties"]["idDireccVento"] == 9:
            d["properties"]["idDireccVento"] = 0
        res.append(
            (
                Station(
                    id=d["properties"]["idEstacao"],
                    latitude=d["geometry"]["coordinates"][0],
                    longitude=d["geometry"]["coordinates"][1],
                    location=d["properties"]["localEstacao"],
                ),
                Measurement(**d["properties"]),
            )
        )

    logger.debug("Measurements acquired successfully")

    if not res:
        logger.error("No new measurements were found on IPMA.pt")
        raise RuntimeError("No Measurements found on IPMA")

    return res


async def post_measurements(
    session: ClientSession, measurements: List[Tuple[Station, Measurement]]
):
    logger.debug("Posting received measurements")

    url = f"{settings.hono.http_adapter}telemetry"

    for station, measurement in measurements:
        logger.debug("Posting measurement for {}", station.id)
        resp = await session.post(
            url,
            json={
                "topic": f"{settings.hono.tenant_id}/metereology:{station.id}/things/twin/commands/modify",
                "path": "/",
                "headers": {},
                "value": {
                    "policyId": settings.hono.policy_id,
                    "attributes": station.model_dump(),
                    "features": {
                        "metereology": {"properties": measurement.model_dump()}
                    },
                },
            },
            ssl=settings.env == Environment.PROD,
        )

        try:
            resp.raise_for_status()
        except ClientResponseError as err:
            logger.error(
                "An error has occured while updating digital twin with id {}, status={}, message={}",
                station.id,
                err.status,
                err.message,
            )


async def main():
    # TODO: remove authentication details from source code
    auth = BasicAuth(
        login=f"{settings.hono.device_id}@{settings.hono.tenant_id}",
        password=settings.hono.passwd,
    )
    async with ClientSession(auth=auth) as session:
        await create_hono_device(session)
        # while True:
        measurements = await get_measurements(session)
        await post_measurements(session, measurements)
        #     await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
