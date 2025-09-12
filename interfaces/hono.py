from hashlib import sha512

from aiohttp import ClientResponseError, ClientSession
from loguru import logger

from settings import Environment, settings


class HonoDevice:
    def __init__(self, session: ClientSession):
        self.session = session
        self.id = settings.hono.device_id
        self.tenant = settings.hono.tenant_id
        self.passwd = settings.hono.passwd

    async def create_hono_device(self):
        logger.debug("Creating device in Hono")
        # If the device exists in the registry, there is no need to create one
        try:
            url = f"{settings.hono.device_registry}v1/devices/{self.tenant}/{self.id}"
            logger.debug("The url is {}", url)
            req = await self.session.post(
                url,
                ssl=settings.env == Environment.PROD,
            )
            req.raise_for_status()
        except ClientResponseError as e:
            if e.status == 409:  # Conflict
                logger.info("The metereology device already existed in Hono")
                return

            logger.error("An error occured while creating the device: {}", e.message)
            raise RuntimeError("The device could not be created")

        try:
            await self.session.put(
                url=f"{settings.hono.device_registry}v1/credentials/{self.tenant}/{self.id}",
                headers={"content-type": "application/json"},
                json=[
                    {
                        "type": "hashed-password",
                        "auth-id": f"{self.id}",
                        "secrets": [
                            {
                                "hash-function": "sha-512",
                                "pwd-hash": sha512(
                                    self.passwd.encode("utf-8")
                                ).hexdigest(),
                            }
                        ],
                    }
                ],
                ssl=settings.env == Environment.PROD,
            )
        except ClientResponseError as e:
            logger.error(
                "An error occured while creating the device's credentials: {}",
                e.message,
            )

            await self.session.delete(
                f"{settings.hono.device_registry}v1/devices/{self.tenant}/{self.id}",
                ssl=settings.env == Environment.PROD,
            )

            raise RuntimeError("The device's credentials could not be created")

    async def send_telemetry(self, message: dict):
        url = f"{settings.hono.http_adapter}telemetry"
        resp = await self.session.post(
            url,
            json=message,
            ssl=settings.env == Environment.PROD,
        )

        try:
            resp.raise_for_status()
        except ClientResponseError as err:
            logger.error(
                "An error has occured while sending telemetry.\n\t Status: {}\n\t Msg: {}",
                err.status,
                err.message,
            )
