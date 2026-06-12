"""
MongoDB Client
MongoDB 客户端：连接管理、索引创建
"""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from app.config import settings

logger = logging.getLogger(__name__)


class MongoClientManager:

    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None
        self._enabled = settings.mongodb_enabled

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    async def init(self) -> None:
        if not self._enabled:
            logger.info("MongoDB is disabled, skipping initialization")
            return
        try:
            self._client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,
            )
            self._db = self._client[settings.mongodb_db_name]
            await self._client.admin.command("ping")
            await self._ensure_indexes()
            logger.info("MongoDB initialized successfully at %s", settings.mongodb_url)
        except Exception:
            logger.warning("Failed to initialize MongoDB, disabling", exc_info=True)
            self._enabled = False
            if self._client:
                self._client.close()
            self._client = None
            self._db = None

    async def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    async def _ensure_indexes(self) -> None:
        try:
            op_logs = self._db["agent_operation_logs"]
            await op_logs.create_index(
                [("conversation_id", 1), ("created_at", -1)],
                name="idx_conv_time",
            )
            await op_logs.create_index(
                [("agent_id", 1), ("created_at", -1)],
                name="idx_agent_time",
            )
            await op_logs.create_index(
                [("operation_type", 1), ("created_at", -1)],
                name="idx_optype_time",
            )
            await op_logs.create_index(
                [("created_at", -1)],
                name="idx_created_at",
            )

            conv_events = self._db["conversation_events"]
            await conv_events.create_index(
                [("conversation_id", 1), ("created_at", -1)],
                name="idx_conv_time",
            )
            await conv_events.create_index(
                [("event_type", 1), ("created_at", -1)],
                name="idx_event_time",
            )
            await conv_events.create_index(
                [("created_at", -1)],
                name="idx_created_at",
            )

            transcripts = self._db["conversation_transcripts"]
            await transcripts.create_index(
                [("conversation_id", 1)],
                name="idx_conversation_id",
                unique=True,
            )
            await transcripts.create_index(
                [("created_at", -1)],
                name="idx_created_at",
            )
        except Exception:
            logger.warning("Failed to create MongoDB indexes", exc_info=True)

    def get_collection(self, name: str) -> AsyncIOMotorCollection | None:
        if self._db is None:
            return None
        return self._db[name]

    def get_operation_logs(self) -> AsyncIOMotorCollection | None:
        return self.get_collection("agent_operation_logs")

    def get_conversation_events(self) -> AsyncIOMotorCollection | None:
        return self.get_collection("conversation_events")


mongo_client = MongoClientManager()