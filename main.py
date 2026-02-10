import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every
from loguru import logger

from interfaces.equivia import get_equivia
from interfaces.ipma import get_measurements
from interfaces.waze import get_traffic_data
from interfaces.signs import get_signs
from interfaces.barriers import get_barrier
from settings import settings, DeviceType
from storage.device import DevicesSingleton
from storage.session import SessionSingleton
from storage.station import StationSingleton


async def batch_cooldown(i: int):
    if i % 100 == 0:
        logger.info(
            "{} requests sent in total, cooling down. Will send another 100 requests in 5 seconds",
            i,
        )
        await asyncio.sleep(5)

    return i + 1


@repeat_every(seconds=settings.polling_interval)
async def update_meteo() -> None:
    logger.info("Updating metereology stations' information")
    measurements = await get_measurements()
    logger.debug("Got measurements from IPMA")

    data = [station for station, _ in measurements]
    await StationSingleton.set_stations(data)

    logger.debug("Posting received measurements")
    meteo = DevicesSingleton.get_device(DeviceType.METEO)
    if meteo is None:
        logger.error("Meteo device not found. Cannot update measurements.")
        return

    for station, measurement in measurements:
        logger.debug("Updating information for {}", station.id)
        await meteo.modify(station, measurement)


@repeat_every(seconds=settings.polling_interval)
async def update_traffic() -> None:
    logger.info("Updating traffic stations' information")
    traffic_device = DevicesSingleton.get_device(DeviceType.TRAFFIC)
    if traffic_device is None:
        logger.error("Traffic device not found. Cannot update measurements.")
        return

    tasks = []
    for toll in settings.tolls:
        logger.debug("Fetching data for {}", toll.name)
        tasks.append(get_traffic_data(toll.latitude, toll.longitude, toll.area_radius))

    traffic_data = await asyncio.gather(*tasks)
    for i, toll in enumerate(settings.tolls):
        logger.debug("Updating information for {}", toll.name)
        await traffic_device.modify(toll, traffic_data[i])


async def update_signs() -> None:
    logger.info("Updating road sign information")
    sign_device = DevicesSingleton.get_device(DeviceType.SIGN)
    if sign_device is None:
        logger.error("Sign device not found. Cannot update road sign data.")
        return

    signs = get_signs()
    logger.debug("Successfully got all the signs")
    i = 1
    for sign in signs:

        logger.debug("Updating sign {}", f"{sign.type}-{sign.objectID}")
        await sign_device.modify(None, sign)
        i = await batch_cooldown(i)

    logger.debug("Finished updating all the signs")


async def update_barriers() -> None:
    logger.info("Updating barrier information")
    barrier_device = DevicesSingleton.get_device(DeviceType.BARRIER)
    if barrier_device is None:
        logger.error("Barrier device not found. Cannot update road sign data.")
        return

    barriers = get_barrier()
    logger.debug("Successfully got all the barriers")
    i = 1
    for barrier in barriers:

        logger.debug("Updating barrier {}", barrier.objectID)
        await barrier_device.modify(None, barrier)
        await asyncio.sleep(0.01)
        i = await batch_cooldown(i)

    logger.debug("Finished updating all the barriers")


async def update_equivia() -> None:
    logger.info("Updating equivia information")
    equivia_device = DevicesSingleton.get_device(DeviceType.EQUIVIA)
    if equivia_device is None:
        logger.error("Equivia device not found. Cannot update road feature data.")
        return

    equivia = get_equivia()
    logger.debug("Successfully got all the road features")
    i = 1
    for thing in equivia:

        logger.debug("Updating road-feature {}", f"{thing.type}-{thing.object_id}")
        await equivia_device.modify(None, thing)
        i = await batch_cooldown(i)

    logger.debug("Finished updating all the road features")


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("STARTUP: Creating Hono devices")

    logger.debug("Existing devices: {}", settings.devices)
    for device in settings.devices:
        hono_conn = DevicesSingleton.add_device(device)

        logger.debug("creating device {}", device.type.value)
        await hono_conn.create_hono_device()

    logger.info("Hono devices created successfully")

    asyncio.create_task(update_meteo())
    # asyncio.create_task(update_traffic())
    # asyncio.create_task(update_signs())
    # asyncio.create_task(update_barriers())
    # asyncio.create_task(update_equivia())

    yield  # Run the main application loop

    logger.info("Closing AioHttp session")
    await SessionSingleton.close_session()
    logger.warning("Stopping async event loop")


app = FastAPI(lifespan=lifespan)


@app.get("/meteorology")
async def get_closest_stations(lat: float, lon: float):
    device = DevicesSingleton.get_device(DeviceType.METEO)
    if device is None:
        raise HTTPException(
            status_code=503, detail="No stations are currently available"
        )

    return [
        f"{device.id}:{station.id}"
        for station in StationSingleton.get_closest_stations(lat, lon)
    ]
