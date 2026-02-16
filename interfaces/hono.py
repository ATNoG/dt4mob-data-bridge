import json
import ssl
from base64 import b64encode
from hashlib import sha512
from json import dumps
from ssl import SSLContext
from typing import Optional

from aiohttp import BasicAuth, ClientResponseError, ClientSession
from loguru import logger
from pydantic import BaseModel

from settings import Environment, settings


class HonoDevice:
    def __init__(
        self,
        session: ClientSession,
        id: str,
        policyId: str,
        passwd: Optional[str] = None,
        cert_path: Optional[str] = None,
    ):
        self.session = session
        self._passwd = passwd
        self._cert_path = cert_path
        self._ssl_context: Optional[SSLContext] = None
        self._auth: Optional[BasicAuth] = None

        # Set up authentication - exactly one of passwd or cert_path is guaranteed by DeviceSettings validator
        if passwd is not None:
            self._auth = BasicAuth(
                login=f"{id}@{settings.hono.tenant_id}",
                password=passwd,
            )
        else:
            # Certificate authentication - cert_path is not None (validated in DeviceSettings)
            assert cert_path is not None
            self._ssl_context = ssl.create_default_context()
            self._ssl_context.load_cert_chain(cert_path)
            # Load Hono server certificate for verification if provided
            if settings.hono.server_cert_path:
                self._ssl_context.load_verify_locations(settings.hono.server_cert_path)

        self.tenant = settings.hono.tenant_id
        self.id = id
        self.policyId = policyId

    def _get_ssl(self) -> "SSLContext | bool":
        """Get SSL context for requests."""
        if self._ssl_context is not None:
            return self._ssl_context
        return settings.env == Environment.PROD

    async def create_hono_device(self) -> None:
        logger.debug(
            "Creating device in Hono with id {} on tenant {}", self.id, self.tenant
        )
        # If the device exists in the registry, there is no need to create one
        try:
            url = f"{settings.hono.device_registry}v1/devices/{self.tenant}/{self.id}"
            req = await self.session.post(
                url,
                auth=self._auth,
                ssl=self._get_ssl(),
            )
            req.raise_for_status()
        except ClientResponseError as e:
            if e.status == 409:  # Conflict
                logger.info("The device {} already existed in Hono", self.id)
                return

            logger.error("An error occured while creating the device: {}", e.message)
            raise RuntimeError("The device could not be created")

        # Only create credentials for password-based auth
        if self._passwd is not None:
            try:
                json = [
                    {
                        "type": "hashed-password",
                        "auth-id": f"{self.id}",
                        "secrets": [
                            {
                                "hash-function": "sha-512",
                                "pwd-hash": b64encode(
                                    sha512(self._passwd.encode("utf-8")).digest()
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
                    ssl=self._get_ssl(),
                )
            except ClientResponseError as e:
                logger.error(
                    "An error occured while creating the device's credentials: {}",
                    e.message,
                )

                await self.session.delete(
                    f"{settings.hono.device_registry}v1/devices/{self.tenant}/{self.id}",
                    auth=self._auth,
                    ssl=self._get_ssl(),
                )

                raise RuntimeError("The device's credentials could not be created")

    async def send_telemetry(self, message: BaseModel) -> None:
        url = f"{settings.hono.http_adapter}telemetry"

        jason = message.model_dump(exclude_none=True)

        logger.debug("Sending the payload {}", json.dumps(jason))

        resp = await self.session.post(
            url,
            json=jason,
            auth=self._auth,
            ssl=self._get_ssl(),
        )

        try:
            resp.raise_for_status()
        except ClientResponseError as err:
            if err.status == 413:
                dump = dumps(jason)
                logger.error(
                    "The entity is too large. \n\t n\t Size: {}",
                    len(dump.encode("utf-8")),
                )

                print_size("root", jason)

            else:
                logger.error(
                    "An error has occured while sending telemetry.\n\t Status: {}\n\t Msg: {}",
                    err.status,
                    err.message,
                )


def print_size(k: str, obj: "object", identation: int = 0) -> None:
    size = len(dumps(obj))
    if size > 1500:
        logger.critical(
            "{} {} - Size: {}, Type: {}", "\t" * identation, k, size, type(obj)
        )
    else:
        logger.debug(
            "{} {} - Size: {}, Type: {}", "\t" * identation, k, size, type(obj)
        )
    if isinstance(obj, dict):
        for key, v in obj.items():
            print_size(str(key), v, identation + 1)
