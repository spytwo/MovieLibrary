import redis.asyncio as redis

from movielibrary.settings import settings

redis_client = redis.from_url(
    settings.redis_url,
)


async def close_redis():
    await redis_client.aclose()
