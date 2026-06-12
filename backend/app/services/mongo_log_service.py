"""
MongoDB Log Service
MongoDB 日志服务：Agent操作日志 + 对话事件存储
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.services.mongo_client import mongo_client

logger = logging.getLogger(__name__)


class MongoLogService:

    async def write_operation_log(
        self,
        log_id: str,
        conversation_id: str,
        agent_id: str,
        agent_name: str,
        operation_type: str,
        operation_detail: dict[str, Any],
        parent_log_id: str | None = None,
        duration_ms: int | None = None,
    ) -> bool:
        if not mongo_client.enabled:
            return False
        try:
            col = mongo_client.get_operation_logs()
            if col is None:
                return False
            doc = {
                "log_id": log_id,
                "conversation_id": conversation_id,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "operation_type": operation_type,
                "operation_detail": operation_detail,
                "parent_log_id": parent_log_id,
                "duration_ms": duration_ms,
                "created_at": datetime.now(timezone.utc),
            }
            await col.insert_one(doc)
            return True
        except Exception:
            logger.warning("MongoDB write_operation_log failed", exc_info=True)
            return False

    async def write_conversation_event(
        self,
        conversation_id: str,
        event_type: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        agent_name: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> bool:
        if not mongo_client.enabled:
            return False
        try:
            col = mongo_client.get_conversation_events()
            if col is None:
                return False
            doc = {
                "conversation_id": conversation_id,
                "event_type": event_type,
                "user_id": user_id,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "detail": detail or {},
                "created_at": datetime.now(timezone.utc),
            }
            await col.insert_one(doc)
            return True
        except Exception:
            logger.warning("MongoDB write_conversation_event failed", exc_info=True)
            return False

    async def query_operation_logs(
        self,
        conversation_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not mongo_client.enabled:
            return []
        try:
            col = mongo_client.get_operation_logs()
            if col is None:
                return []
            cursor = col.find({"conversation_id": conversation_id}).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            for doc in docs:
                doc["_id"] = str(doc["_id"])
                if isinstance(doc.get("created_at"), datetime):
                    doc["created_at"] = doc["created_at"].isoformat()
            return docs
        except Exception:
            logger.warning("MongoDB query_operation_logs failed", exc_info=True)
            return []

    async def query_conversation_events(
        self,
        conversation_id: str,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not mongo_client.enabled:
            return []
        try:
            col = mongo_client.get_conversation_events()
            if col is None:
                return []
            query: dict[str, Any] = {"conversation_id": conversation_id}
            if event_type:
                query["event_type"] = event_type
            cursor = col.find(query).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            for doc in docs:
                doc["_id"] = str(doc["_id"])
                if isinstance(doc.get("created_at"), datetime):
                    doc["created_at"] = doc["created_at"].isoformat()
            return docs
        except Exception:
            logger.warning("MongoDB query_conversation_events failed", exc_info=True)
            return []

    async def archive_conversation_transcript(
        self,
        conversation_id: str,
        messages: list[dict[str, Any]],
        operation_logs: list[dict[str, Any]],
        events: list[dict[str, Any]],
    ) -> bool:
        if not mongo_client.enabled:
            return False
        try:
            col = mongo_client.get_collection("conversation_transcripts")
            if col is None:
                return False
            doc = {
                "conversation_id": conversation_id,
                "messages": messages,
                "operation_logs": operation_logs,
                "events": events,
                "created_at": datetime.now(timezone.utc),
            }
            await col.replace_one(
                {"conversation_id": conversation_id},
                doc,
                upsert=True,
            )
            return True
        except Exception:
            logger.warning("MongoDB archive_conversation_transcript failed", exc_info=True)
            return False

    async def get_conversation_transcript(
        self,
        conversation_id: str,
    ) -> dict[str, Any] | None:
        if not mongo_client.enabled:
            return None
        try:
            col = mongo_client.get_collection("conversation_transcripts")
            if col is None:
                return None
            doc = await col.find_one({"conversation_id": conversation_id})
            if doc and "_id" in doc:
                doc["_id"] = str(doc["_id"])
            if doc and isinstance(doc.get("created_at"), datetime):
                doc["created_at"] = doc["created_at"].isoformat()
            return doc
        except Exception:
            logger.warning("MongoDB get_conversation_transcript failed", exc_info=True)
            return None

    async def aggregate_operation_stats(
        self,
        conversation_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        if not mongo_client.enabled:
            return []
        try:
            col = mongo_client.get_operation_logs()
            if col is None:
                return []
            match: dict[str, Any] = {}
            if conversation_id:
                match["conversation_id"] = conversation_id
            if start_time or end_time:
                time_filter: dict[str, Any] = {}
                if start_time:
                    time_filter["$gte"] = start_time
                if end_time:
                    time_filter["$lte"] = end_time
                if time_filter:
                    match["created_at"] = time_filter
            pipeline = [
                {"$match": match},
                {
                    "$group": {
                        "_id": "$operation_type",
                        "count": {"$sum": 1},
                        "avg_duration_ms": {"$avg": "$duration_ms"},
                        "max_duration_ms": {"$max": "$duration_ms"},
                    }
                },
                {"$sort": {"count": -1}},
            ]
            cursor = col.aggregate(pipeline)
            return await cursor.to_list(length=50)
        except Exception:
            logger.warning("MongoDB aggregate_operation_stats failed", exc_info=True)
            return []


mongo_log_service = MongoLogService()