import asyncio

from loguru import logger


async def batch_cooldown(i: int) -> int:
    if i % 100 == 0:
        logger.info(
            "{} requests sent in total, cooling down. Will send another 100 requests in 2 seconds",
            i,
        )
        await asyncio.sleep(2)

    return i + 1
