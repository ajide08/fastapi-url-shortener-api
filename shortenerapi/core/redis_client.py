from typing import Optional
from shortenerapi.core.config import get_settings
import redis.asyncio as redis

settings = get_settings()

class RedisClient:
    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.client.ping()
            print(f'Connected to redis at {settings.REDIS_URL}')
        except Exception as e:
            print(f'Redis Connection failed: {e}')
            print('Continuing without Redis (fallback to database only)')
            self.client = None

    async def disconnect(self):
        if self.client:
            await self.client.close()
            print('Disconnected from Redis')

    async def set_url(self, short_code: str, original_url: str, ttl_seconds: Optional[int] = None):
        if not self.client:
            return None

        if ttl_seconds is not None and ttl_seconds <= 0:
            return None

        key = f"url:{short_code}"
        ttl = ttl_seconds if ttl_seconds is not None else settings.REDIS_TTL_SECONDS
        await self.client.set(key, original_url, ex=ttl)

    async def get_url(self, short_code: str) -> Optional[str]:
        if not self.client:
            return None

        key = f"url:{short_code}"
        url = await self.client.get(key)
        if url:
            print(f"Redis cache hit: {short_code}")
        else:
            print(f"Redis cache miss: {short_code}")
        return url

    async def delete_url(self, short_code: str):
        if not self.client:
            return

        await self.client.delete(f"url:{short_code}")
        await self.client.delete(f"clicks:{short_code}")

    async def increment_clicks(self, short_code: str):
        if self.client:
            await self.client.incr(f"clicks:{short_code}")

    async def get_clicks(self, short_code: str) -> int:
        if not self.client:
            return 0

        clicks = await self.client.get(f"clicks:{short_code}")
        return int(clicks) if clicks else 0

    async def add_to_recent(self, short_code: str):
        if self.client:
            await self.client.lpush("recent:urls", short_code)
            await self.client.ltrim("recent:urls", 0, 99)

    async def get_recent(self, limit: int = 10) -> list:
        if not self.client:
            return []
        return await self.client.lrange("recent:urls", 0, limit - 1)

    async def check_rate_limit(self, client_ip: str, limit: int = 100, window: int = 3600) -> bool:
        if not self.client:
            return True

        key = f"rate_limit:{client_ip}"
        current = await self.client.get(key)
        if current is None:
            await self.client.setex(key, window, 1)
            return True

        if int(current) >= limit:
            return False
        await self.client.incr(key)
        return True

    async def get_url_stats(self, short_code: str) -> Optional[dict]:
        if not self.client:
            return None

        url = await self.get_url(short_code)
        if not url:
            return None

        clicks = await self.get_clicks(short_code)
        ttl = await self.client.ttl(f"url:{short_code}")
        return {
            "short_code": short_code,
            "original_url": url,
            "clicks": clicks,
            "ttl_seconds": ttl if ttl > 0 else None
        }

# Create a single instance
redis_client = RedisClient()