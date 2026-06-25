import json
import ssl
from json import dumps

from aiohttp import ClientResponseError, ClientSession
from loguru import logger
from pydantic import BaseModel

from settings import settings


class HonoDevice:
    def __init__(self, cert_path: str, private_key: str):
        self.session = ClientSession()
        self._ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self._ssl_context.load_cert_chain(cert_path, private_key)

        # Load Hono server certificate for verification if provided
        if settings.hono.server_cert_path:
            self._ssl_context.load_verify_locations(settings.hono.server_cert_path)

        self.tenant = settings.hono.tenant_id

    async def send_telemetry(self, message: BaseModel) -> None:
        url = f"{settings.hono.http_adapter}telemetry"

        jason = message.model_dump(exclude_none=True)

        logger.debug("Sending the payload {}", json.dumps(jason))

        dump = dumps(jason)
        if len(dump.encode("utf-8")) > 4000:
            logger.error(
                "The entity is too large. Not sending the payload \n\t\n\t Size: {}",
                len(dump.encode("utf-8")),
            )
            return

        async with self.session.post(
            url,
            json=jason,
            ssl=self._ssl_context,
        ) as resp:
            try:
                resp.raise_for_status()
            except ClientResponseError as err:
                if err.status == 413:
                    dump = dumps(jason)
                    logger.error(
                        "The entity is too large. \n\t \n\t Size: {}",
                        len(dump.encode("utf-8")),
                    )

                    print_size("root", jason)

                else:
                    logger.error(
                        "An error has occured while sending telemetry.\n\t Status: {}\n\t Msg: {}",
                        err.status,
                        err.message,
                    )

    async def close_session(self):
        await self.session.close()


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
