import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every
from loguru import logger

from devices.meteo import MeteoDevice
from devices.traffic import TrafficDevice
from interfaces.hono import HonoDevice
from interfaces.ipma import get_measurements
from interfaces.waze import get_traffic_data
from settings import settings
from storage import DevicesSingleton, SessionSingleton, StationSingleton


@repeat_every(seconds=settings.polling_interval)
async def update_meteo() -> None:
    logger.info("Updating metereology stations' information")
    measurements = await get_measurements()
    logger.debug("Got measurements from IPMA")

    data = [station for station, _ in measurements]
    await StationSingleton.set_stations(data)

    logger.debug("Posting received measurements")
    meteo = DevicesSingleton.get_device("meteo")
    assert isinstance(meteo, MeteoDevice)

    for station, measurement in measurements:
        logger.debug("Updating information for {}", station.id)
        await meteo.modify(station, measurement)


@repeat_every(seconds=settings.polling_interval)
async def update_traffic() -> None:
    logger.info("Updating traffic stations' information")
    traffic_device = DevicesSingleton.get_device("traffic")
    assert isinstance(traffic_device, TrafficDevice)

    for toll in settings.tolls:
        logger.debug("Updating information for {}", toll.name)
        data = await get_traffic_data(toll.latitude, toll.longitude)
        await traffic_device.modify(toll, data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning("Starting async event loop")
    loop = asyncio.new_event_loop()

    logger.info("STARTUP: Creating Hono devices")

    logger.debug("Existing devices: {}", settings.devices)
    for device in settings.devices:
        hono_conn = HonoDevice(
            SessionSingleton.get_session(), device.id, device.passwd, device.policy_id
        )

        match device.id:
            case "meteo":
                DevicesSingleton.add_device(MeteoDevice(hono_conn))
            case "traffic":
                DevicesSingleton.add_device(TrafficDevice(hono_conn))
            case _:
                raise RuntimeError("This type of device has not yet been implemented")

        logger.debug("creating device {}", device.id)
        await hono_conn.create_hono_device()

    logger.info("Hono devices created successfully")

    await update_meteo()
    await update_traffic()

    yield

    logger.info("Closing AioHttp session")
    await SessionSingleton.close_session()
    logger.warning("Stopping async event loop")
    loop.stop()
    loop.close()


app = FastAPI(lifespan=lifespan)


@app.get("/meteorology")
async def get_closest_stations(lat: float, lon: float):
    device = DevicesSingleton.get_device("meteo")
    if device is None:
        raise HTTPException(
            status_code=503, detail="No stations are currently available"
        )

    return [
        f"{device.id}:{station.id}"
        for station in StationSingleton.get_closest_stations(lat, lon)
    ]
