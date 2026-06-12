"""
Redis Connection Management
Redis连接管理
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis

from app.config import settings


class RedisManager:
    """Redis连接管理器"""

    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def init(self) -> None:
        """初始化Redis连接池"""
        self._pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
        self._client = Redis(connection_pool=self._pool)

    async def close(self) -> None:
        """关闭Redis连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None

    @property
    def client(self) -> Redis:
        """获取Redis客户端"""
        if self._client is None:
            raise RuntimeError("Redis not initialized")
        return self._client

    async def get(self, key: str) -> str | None:
        """获取值"""
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """设置值"""
        return await self.client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    async def delete(self, *keys: str) -> int:
        """删除键"""
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.client.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        return await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """获取剩余生存时间"""
        return await self.client.ttl(key)

    async def incr(self, key: str) -> int:
        """递增"""
        return await self.client.incr(key)

    async def hset(self, name: str, mapping: dict[str, Any]) -> int:
        """设置哈希字段"""
        return await self.client.hset(name, mapping=mapping)

    async def hget(self, name: str, key: str) -> str | None:
        """获取哈希字段"""
        return await self.client.hget(name, key)

    async def hgetall(self, name: str) -> dict[str, str]:
        """获取所有哈希字段"""
        return await self.client.hgetall(name)

    async def lpush(self, name: str, *values: str) -> int:
        """向左推入列表"""
        return await self.client.lpush(name, *values)

    async def rpop(self, name: str) -> str | None:
        """向右弹出列表"""
        return await self.client.rpop(name)

    @asynccontextmanager
    async def pipeline(self) -> AsyncGenerator[Redis, None]:
        """获取管道上下文"""
        async with self.client.pipeline(transaction=True) as pipe:
            yield pipe

    async def publish(self, channel: str, message: str) -> int:
        """发布消息"""
        return await self.client.publish(channel, message)

    async def get_message(self) -> dict[str, Any] | None:
        """获取消息"""
        msg = await self.client.get_message()
        if msg:
            return {"channel": msg.channel, "data": msg.data, "type": msg.type}
        return None


redis_manager = RedisManager()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """获取Redis客户端依赖"""
    yield redis_manager.client


def get_rate_limit_key(identifier: str, endpoint: str) -> str:
    """生成限流键"""
    return f"rate_limit:{endpoint}:{identifier}"
