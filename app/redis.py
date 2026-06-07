from typing import AsyncGenerator
import redis.asyncio as aioredis

from redis.asyncio import Redis

from app.settings import settings

redis_client = aioredis.from_url(settings.redis_url)


async def get_redis() -> AsyncGenerator[Redis, None]:
    yield redis_client
