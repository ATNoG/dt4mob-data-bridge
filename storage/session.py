from typing import Optional
from aiohttp import ClientSession


class SessionSingleton:
    client: Optional[ClientSession] = None

    @classmethod
    def get_session(cls) -> ClientSession:
        if cls.client is None:
            cls.client = ClientSession()

        return cls.client

    @classmethod
    async def close_session(cls) -> None:
        if cls.client:
            await cls.client.close()
            cls.client = None
