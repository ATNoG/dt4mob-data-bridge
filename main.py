import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every
from loguru import logger

from interfaces.barriers import get_barrier
from interfaces.equivia import get_equivia
from interfaces.ipma import get_meteorology_measurements, get_meteorology_warnings
from interfaces.signs import get_signs
from interfaces.waze import get_traffic_data
from models.meteo import WarningArea
from settings import DeviceType, settings
from storage.device import DevicesSingleton
from storage.session import SessionSingleton
from storage.station import StationSingleton


def is_device_active(device_type: DeviceType) -> bool:
    return any(device.type == device_type for device in settings.devices)


async def batch_cooldown(i: int) -> int:
    if i % 100 == 0:
        logger.info(
            "{} requests sent in total, cooling down. Will send another 100 requests in 5 seconds",
            i,
        )
        await asyncio.sleep(5)

    return i + 1


async def populate_warning_areas() -> None:
    logger.debug("Populating the warning areas in the Station Singleton")
    session = SessionSingleton.get_session()

    req = await session.get("https://api.ipma.pt/open-data/distrits-islands.json")
    try:
        req.raise_for_status()
    except Exception as e:
        logger.error(
            "An error has occured while getting the warning areas from IPMA API, {}", e
        )
        return

    data = await req.json()
    areas = [WarningArea.model_validate(area) for area in data["data"]]

    logger.debug("Successfully acquired the warning areas {}", areas)
    await StationSingleton.set_warning_areas(areas)
    logger.debug("Successfully stored the warning areas")


async def populate_stations() -> None:
    logger.info("Updating metereology stations' information")
    measurements = await get_meteorology_measurements()
    logger.debug("Got measurements from IPMA")

    stations = [station for station, _ in measurements]
    await StationSingleton.set_stations(stations)


async def update_meteo() -> None:
    logger.info("Updating metereology stations' information")
    measurements = await get_meteorology_measurements()
    logger.debug("Got measurements from IPMA")

    stations = [station for station, _ in measurements]
    await StationSingleton.set_stations(stations)

    logger.debug("Posting received measurements")
    meteo = DevicesSingleton.get_device(DeviceType.METEO)
    if meteo is None:
        logger.error("Meteo device not found. Cannot update measurements.")
        return

    for station, measurement in measurements:
        logger.debug("Updating measurements for {}", station.id)
        await meteo.modify(station, measurement)


@repeat_every(seconds=settings.polling_interval)
async def loop_meteo():
    await update_meteo()


async def update_meteo_warnings() -> None:
    warnings = await get_meteorology_warnings()
    meteo = DevicesSingleton.get_device(DeviceType.METEO)
    if meteo is None:
        logger.error("Meteo device not found. Cannot update measurements.")
        return

    for station, warning in warnings.items():
        dump = [warn.model_dump() for warn in warning]
        logger.debug("Updating information for {} - {}", station.id, dump)
        message = meteo.modify_message(str(station.id))
        message.path = "/features/events"
        message.value = {"properties": {"warnings": dump}}  # ty:ignore[invalid-assignment]

        await meteo._hono.send_telemetry(message)


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
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("STARTUP: Creating Hono devices")

    logger.debug("Existing devices: {}", settings.devices)
    for device in settings.devices:
        hono_conn = DevicesSingleton.add_device(device)

        logger.debug("creating device {}", device.type.value)
        await hono_conn.create_hono_device()

    logger.info("Hono devices created successfully")

    await populate_warning_areas()
    await populate_stations()

    if is_device_active(DeviceType.METEO):
        await update_meteo()
        await update_meteo_warnings()
    #     asyncio.create_task(loop_meteo())
    #
    # if is_device_active(DeviceType.TRAFFIC):
    #     asyncio.create_task(update_traffic())
    # if is_device_active(DeviceType.SIGN):
    #     asyncio.create_task(update_signs())
    # if is_device_active(DeviceType.BARRIER):
    #     asyncio.create_task(update_barriers())
    # if is_device_active(DeviceType.EQUIVIA):
    #     asyncio.create_task(update_equivia())

    yield  # Run the main application loop

    logger.info("Closing AioHttp session")
    await SessionSingleton.close_session()
    logger.warning("Stopping async event loop")


app = FastAPI(lifespan=lifespan)


@app.get("/meteorology")
async def get_closest_stations(lat: float, lon: float) -> list[str]:
    device = DevicesSingleton.get_device(DeviceType.METEO)
    if device is None:
        raise HTTPException(
            status_code=503, detail="No stations are currently available"
        )

    stations = await StationSingleton.get_closest_stations(lat, lon)
    return [f"{device.id}:{station.id}" for station in stations]
