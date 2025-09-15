import asyncio
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from loguru import logger
from contextlib import asynccontextmanager

from interfaces.hono import HonoDevice
from interfaces.ipma import get_measurements
from interfaces.waze import get_traffic_data
from settings import settings
from storage.stations import StationSingleton
from session import SessionSingleton

devices: dict[str, HonoDevice] = {}


@repeat_every(seconds=settings.polling_interval)
async def update_meteo() -> None:
    logger.info("Updating metereology stations' information")
    measurements = await get_measurements()
    logger.debug("Got measurements from IPMA")
    data = [station for station, _ in measurements]
    await StationSingleton.set_stations(data)
    logger.debug("Posting received measurements")
    meteo = devices.get("meteo")
    assert meteo is not None

    for station, measurement in measurements:
        logger.debug("Updating information for {}", station.id)
        await meteo.send_telemetry(station.id, station.create_message(measurement))


@repeat_every(seconds=settings.polling_interval)
async def update_traffic() -> None:
    logger.info("Updating traffic stations' information")
    logger.debug("Tolls: {}", settings.tolls)
    traffic_device = devices.get("traffic")
    assert traffic_device is not None
    for toll in settings.tolls:
        logger.debug("Updating information for {}", toll.name)
        data = await get_traffic_data(toll.latitude, toll.longitude)
        message = {
            **data.create_message(),
            "attributes": {
                "meteo_stations": [
                    f"{devices['meteo'].id}:{station.id}"
                    for station in StationSingleton.get_closest_stations(
                        toll.latitude, toll.longitude
                    )
                ],
                "latitude": toll.latitude,
                "longitude": toll.longitude,
                "name": toll.name,
            },
        }
        await traffic_device.send_telemetry(toll.name, message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning("Starting async event loop")
    loop = asyncio.new_event_loop()

    logger.info("STARTUP: Creating Hono devices")

    global devices
    logger.debug("Existing devices: {}", settings.devices)
    for name, device in settings.devices.items():
        new_device = HonoDevice(
            SessionSingleton.get_session(), device.id, device.passwd, device.policy_id
        )
        devices[name] = new_device
        logger.debug("creating device {}", name)
        await new_device.create_hono_device()

    logger.info("Hono devices created successfully")

    await update_meteo()
    await update_traffic()

    yield

    devices = {}
    logger.info("Closing AioHttp session")
    await SessionSingleton.close_session()
    logger.warning("Stopping async event loop")
    loop.stop()
    loop.close()


app = FastAPI(lifespan=lifespan)


@app.get("/meteorology")
async def get_closest_stations(lat: float, lon: float):
    return [
        f"{settings.devices['meteo'].id}:{station.id}"
        for station in StationSingleton.get_closest_stations(lat, lon)
    ]
