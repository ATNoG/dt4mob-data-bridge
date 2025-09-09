from aiohttp import BasicAuth, ClientSession
from typing import Optional

from settings import settings


class SessionSingleton:
    client: Optional[ClientSession] = None

    @classmethod
    def get_session(cls) -> ClientSession:
        if cls.client is None:
            auth = BasicAuth(
                login=f"{settings.hono.device_id}@{settings.hono.tenant_id}",
                password=settings.hono.passwd,
            )
            cls.client = ClientSession(auth=auth)

        return cls.client

    @classmethod
    async def close_session(cls):
        if cls.client:
            await cls.client.close()
            cls.client = None
