from hashlib import sha512
import json
from base64 import b64encode

from aiohttp import BasicAuth, ClientResponseError, ClientSession
from loguru import logger

from settings import Environment, settings


class HonoDevice:
    def __init__(self, session: ClientSession, id: str, passwd: str, policyId: str):
        self.session = session
        self._auth = BasicAuth(
            login=f"{id}@{settings.hono.tenant_id}",
            password=passwd,
        )
        self.tenant = settings.hono.tenant_id
        self.id = id
        self.passwd = passwd
        self.policyId = policyId

    async def create_hono_device(self):
        logger.debug(
            "Creating device in Hono with id {} on tenant {}", self.id, self.tenant
        )
        # If the device exists in the registry, there is no need to create one
        try:
            url = f"{settings.hono.device_registry}v1/devices/{self.tenant}/{self.id}"
            req = await self.session.post(
                url,
                auth=self._auth,
                ssl=settings.env == Environment.PROD,
            )
            req.raise_for_status()
        except ClientResponseError as e:
            if e.status == 409:  # Conflict
                logger.info("The device {} already existed in Hono", self.id)
                return

            logger.error("An error occured while creating the device: {}", e.message)
            raise RuntimeError("The device could not be created")

        try:
            json = [
                {
                    "type": "hashed-password",
                    "auth-id": f"{self.id}",
                    "secrets": [
                        {
                            "hash-function": "sha-512",
                            "pwd-hash": b64encode(
                                sha512(self.passwd.encode("utf-8")).digest()
                            ).decode("utf-8"),
                        }
                    ],
                }
            ]

            await self.session.put(
                url=f"{settings.hono.device_registry}v1/credentials/{self.tenant}/{self.id}",
                auth=self._auth,
                json=json,
                headers={"content-type": "application/json"},
                ssl=settings.env == Environment.PROD,
            )
        except ClientResponseError as e:
            logger.error(
                "An error occured while creating the device's credentials: {}",
                e.message,
            )

            await self.session.delete(
                f"{settings.hono.device_registry}v1/devices/{self.tenant}/{self.id}",
                auth=self._auth,
                ssl=settings.env == Environment.PROD,
            )

            raise RuntimeError("The device's credentials could not be created")

    async def send_telemetry(self, device_id, message: dict):
        url = f"{settings.hono.http_adapter}telemetry"
        jason = {
            "topic": f"{self.id}/{device_id}/things/twin/commands/modify",
            "path": "/",
            "headers": {},
            "value": {"policyId": self.policyId, **message},
        }

        resp = await self.session.post(
            url,
            json=jason,
            auth=self._auth,
            ssl=settings.env == Environment.PROD,
        )

        try:
            resp.raise_for_status()
        except ClientResponseError as err:
            logger.error(
                "An error has occured while sending telemetry.\n\t Status: {}\n\t Msg: {} {}",
                err.status,
                err.message,
                f"\n\t Length: {len(json.dumps(jason))}" if err.status == 413 else "",
            )
