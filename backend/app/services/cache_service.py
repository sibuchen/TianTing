"""
Cache-Aside Cache Service
缓存旁路服务
"""

import logging
from typing import Any, Awaitable, Callable

from app.core.redis import redis_manager

logger = logging.getLogger(__name__)


def conversation_cache_key(conversation_id: str) -> str:
    return f"cache:conversation:{conversation_id}"


def session_cache_key(session_id: str) -> str:
    return f"cache:session:{session_id}"


def chat_history_key(conversation_id: str) -> str:
    return f"cache:chat_history:{conversation_id}"


def agent_config_key(agent_id: str) -> str:
    return f"cache:agent_config:{agent_id}"


class CacheAsideService:
    """Cache-Aside 缓存服务"""

    async def get(self, key: str) -> str | None:
        try:
            return await redis_manager.get(key)
        except Exception:
            logger.warning("Cache get failed for key: %s", key, exc_info=True)
            return None

    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        try:
            return await redis_manager.set(key, value, ex=ttl)
        except Exception:
            logger.warning("Cache set failed for key: %s", key, exc_info=True)
            return False

    async def delete(self, *keys: str) -> int:
        if not keys:
            return 0
        try:
            return await redis_manager.delete(*keys)
        except Exception:
            logger.warning("Cache delete failed for keys: %s", keys, exc_info=True)
            return 0

    async def get_or_set(
        self,
        key: str,
        ttl: int,
        factory: Callable[[], Awaitable[str]],
    ) -> str:
        cached = await self.get(key)
        if cached is not None:
            return cached

        value = await factory()
        if value is not None:
            await self.set(key, value, ttl)
        return value

    async def invalidate_pattern(self, pattern: str) -> int:
        try:
            deleted = 0
            async for key in redis_manager.client.scan_iter(match=pattern):
                deleted += await redis_manager.delete(key)
            return deleted
        except Exception:
            logger.warning(
                "Cache invalidate_pattern failed for pattern: %s",
                pattern,
                exc_info=True,
            )
            return 0

    async def list_push(self, key: str, *values: str) -> int:
        try:
            return await redis_manager.client.lpush(key, *values)
        except Exception:
            logger.warning("Cache list_push failed for key: %s", key, exc_info=True)
            return 0

    async def list_range(self, key: str, start: int, end: int) -> list[str]:
        try:
            return await redis_manager.client.lrange(key, start, end)
        except Exception:
            logger.warning("Cache list_range failed for key: %s", key, exc_info=True)
            return []

    async def list_trim(self, key: str, start: int, end: int) -> bool:
        try:
            await redis_manager.client.ltrim(key, start, end)
            return True
        except Exception:
            logger.warning("Cache list_trim failed for key: %s", key, exc_info=True)
            return False

    async def list_len(self, key: str) -> int:
        try:
            return await redis_manager.client.llen(key)
        except Exception:
            logger.warning("Cache list_len failed for key: %s", key, exc_info=True)
            return 0

    async def append_chat_history(
        self,
        conversation_id: str,
        message_json: str,
        max_len: int | None = None,
        ttl: int | None = None,
    ) -> None:
        from app.config import settings

        max_len = max_len or settings.cache_chat_history_max_len
        ttl = ttl or settings.cache_ttl_chat_history

        key = chat_history_key(conversation_id)
        await self.list_push(key, message_json)
        await self.list_trim(key, 0, max_len - 1)
        await redis_manager.client.expire(key, ttl)

    async def get_chat_history(
        self,
        conversation_id: str,
        count: int | None = None,
    ) -> list[str]:
        from app.config import settings

        count = count or settings.cache_chat_history_max_len
        key = chat_history_key(conversation_id)
        return await self.list_range(key, 0, count - 1)


cache_service = CacheAsideService()