import asyncio
from typing import Optional
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from loguru import logger
from contextlib import asynccontextmanager

from interfaces.hono import HonoDevice
from interfaces.ipma import get_measurements
from settings import settings
from storage.stations import StationSingleton
from session import SessionSingleton

hono: Optional[HonoDevice] = None


@repeat_every(seconds=settings.polling_interval)
async def update_meteo() -> None:
    logger.info("Updating metereology stations' information")
    measurements = await get_measurements()
    logger.debug("Got measurements from IPMA")
    data = [station for station, _ in measurements]
    await StationSingleton.set_stations(data)
    assert hono is not None
    logger.debug("Posting received measurements")

    for station, measurement in measurements:
        await hono.send_telemetry(station.create_message(measurement))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning("Starting async event loop")
    loop = asyncio.new_event_loop()

    logger.info("STARTUP: Creating Hono device")

    global hono
    hono = HonoDevice(SessionSingleton.get_session())
    await hono.create_hono_device()

    logger.info("Hono device created successfully")

    logger.info("Updating metereology stations")
    await update_meteo()

    yield
    hono = None
    logger.info("Closing AioHttp session")
    await SessionSingleton.close_session()
    logger.warning("Stopping async event loop")
    loop.stop()
    loop.close()


app = FastAPI(lifespan=lifespan)


@app.get("/metereology")
async def get_closest_stations(lat: float, lon: float):
    return [
        f"{settings.hono.device_id}:{station.id}"
        for station in StationSingleton.get_closest_stations(lat, lon)
    ]
