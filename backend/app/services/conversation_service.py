"""
Conversation Service
会话服务：消息处理/流式生成
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from sqlalchemy import select, update, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConversationNotFoundError,
    ConversationEndedError,
    RateLimitExceededError,
)
from app.core.redis import redis_manager, get_rate_limit_key
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.agent import Agent
from app.schemas.conversation import (
    SessionCreateResponse,
    SessionInfoResponse,
    MessageItem,
    ToolCallItem,
)
from app.config import settings
from app.services.cache_service import (
    cache_service,
    session_cache_key,
    chat_history_key,
)
from app.services.mongo_log_service import mongo_log_service
from app.graph.sync_service import graph_sync_service

logger = logging.getLogger(__name__)


class ConversationService:
    """会话服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(
        self,
        session_id: str | None = None,
        user_id: str | None = None,
        user_name: str | None = None,
        user_avatar: str | None = None,
        channel: str = "web",
    ) -> SessionCreateResponse:
        """创建会话"""
        if not session_id:
            session_id = str(uuid.uuid4())

        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
            user_name=user_name,
            user_avatar=user_avatar,
            status="active",
            handled_by="agent",
            channel=channel,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(conversation)
        await self.db.flush()

        welcome_message = Message(
            conversation_id=conversation.id,
            role="system",
            content="您好！欢迎使用天听智能客服系统，有什么可以帮您的？",
            is_system_message=True,
        )
        self.db.add(welcome_message)

        await self.db.commit()
        await self.db.refresh(conversation)

        try:
            await graph_sync_service.sync_conversation_relation(
                user_id=user_id,
                conversation_id=str(conversation.id),
                agent_id="",
                intent="",
                channel=channel or "web",
            )
        except Exception:
            pass

        try:
            await mongo_log_service.write_conversation_event(
                conversation_id=str(conversation.id),
                event_type="started",
                user_id=user_id,
                detail={"channel": channel},
            )
        except Exception:
            pass

        return SessionCreateResponse(
            session_id=session_id,
            conversation_id=conversation.id,
            status="active",
            channel=channel,
            welcome_message="您好！欢迎使用天听智能客服系统，有什么可以帮您的？",
        )

    async def get_session(
        self, session_id: str
    ) -> tuple[Conversation, list[Message]]:
        cached = await cache_service.get(session_cache_key(session_id))
        if cached:
            try:
                cached_data = json.loads(cached)
                result = await self.db.execute(
                    select(Conversation)
                    .options(selectinload(Conversation.messages))
                    .where(Conversation.id == cached_data["id"])
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    return conversation, conversation.messages
            except (json.JSONDecodeError, KeyError):
                logger.warning(
                    "Corrupted cache for session: %s, falling through to DB",
                    session_id,
                )

        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.session_id == session_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ConversationNotFoundError()

        await cache_service.set(
            session_cache_key(session_id),
            json.dumps(conversation.to_dict(), ensure_ascii=False),
            ttl=settings.cache_ttl_conversation,
        )

        return conversation, conversation.messages

    async def get_session_info(self, session_id: str) -> SessionInfoResponse:
        """获取会话信息"""
        conversation, _ = await self.get_session(session_id)

        return SessionInfoResponse(
            session_id=session_id,
            conversation_id=conversation.id,
            status=conversation.status,
            channel=conversation.channel,
            handled_by=conversation.handled_by,
            message_count=conversation.message_count,
            created_at=conversation.created_at.isoformat() if conversation.created_at else None,
        )

    async def get_messages(
        self,
        session_id: str,
        before: str | None = None,
        limit: int = 50,
    ) -> tuple[list[MessageItem], bool]:
        """获取消息列表"""
        conversation, messages = await self.get_session(session_id)

        query = select(Message).where(
            Message.conversation_id == conversation.id
        )

        if before:
            before_msg_result = await self.db.execute(
                select(Message).where(Message.id == before)
            )
            before_msg = before_msg_result.scalar_one_or_none()
            if before_msg:
                query = query.where(Message.created_at < before_msg.created_at)

        query = query.order_by(Message.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        messages_list = list(result.scalars().all())
        messages_list.reverse()

        has_more = len(messages_list) == limit

        return [
            MessageItem(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at.isoformat() if msg.created_at else None,
                type="text",
                agent_name=msg.agent_name,
                tool_calls=[
                    ToolCallItem(
                        id=tc.get("id", str(uuid.uuid4())),
                        name=tc.get("toolName", ""),
                        arguments=json.dumps(tc.get("arguments", {})),
                        result=str(tc.get("result", "")),
                    )
                    for tc in (msg.tool_calls or [])
                ]
                if msg.tool_calls
                else None,
                is_system_message=msg.is_system_message,
            )
            for msg in messages_list
        ], has_more

    async def check_rate_limit(self, session_id: str) -> None:
        """检查限流"""
        key = get_rate_limit_key(session_id, "chat_message")
        count = await redis_manager.get(key)

        if count and int(count) >= settings.chat_rate_limit_per_minute:
            raise RateLimitExceededError()

        pipe = redis_manager.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        await pipe.execute()

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_id: str | None = None,
        agent_name: str | None = None,
        tool_calls: list[dict] | None = None,
        is_system_message: bool = False,
    ) -> Message:
        """添加消息"""
        conversation, _ = await self.get_session(session_id)

        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            agent_id=agent_id,
            agent_name=agent_name,
            tool_calls=tool_calls,
            is_system_message=is_system_message,
        )
        self.db.add(message)

        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(
                message_count=conversation.message_count + 1,
                updated_at=datetime.now(timezone.utc),
            )
        )

        await self.db.commit()
        await self.db.refresh(message)

        try:
            await mongo_log_service.write_conversation_event(
                conversation_id=str(conversation.id),
                event_type="message_sent",
                agent_id=agent_id,
                agent_name=agent_name,
                detail={"role": role, "content_preview": content[:200] if content else ""},
            )
        except Exception:
            pass

        message_data = json.dumps({
            "id": str(message.id),
            "role": message.role,
            "content": message.content,
            "agent_name": message.agent_name,
            "tool_calls": message.tool_calls,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        })
        await cache_service.append_chat_history(conversation.id, message_data)

        max_messages = int(os.getenv("CONVERSATION_MAX_MESSAGES", "100"))
        await self._trim_old_messages(conversation, max_messages)

        return message

    async def _trim_old_messages(self, conversation: Conversation, max_messages: int) -> None:
        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation.id,
                Message.is_system_message == False,
            )
            .order_by(Message.created_at.asc())
        )
        all_user_messages = list(result.scalars().all())

        current_count = conversation.message_count
        if current_count <= max_messages:
            return

        to_delete_count = current_count - max_messages

        messages_to_delete = all_user_messages[:to_delete_count]
        if not messages_to_delete:
            return

        delete_ids = [msg.id for msg in messages_to_delete]
        await self.db.execute(
            sa_delete(Message).where(Message.id.in_(delete_ids))
        )

        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(message_count=Conversation.message_count - len(delete_ids))
        )

        logger.info(
            f"Trimmed {len(delete_ids)} old messages from conversation {conversation.id}, "
            f"new count: {current_count - len(delete_ids)}"
        )

    async def update_conversation_status(
        self, session_id: str, status: str, handled_by: str | None = None
    ) -> None:
        conversation, _ = await self.get_session(session_id)

        update_data = {"status": status, "updated_at": datetime.now(timezone.utc)}

        if handled_by:
            update_data["handled_by"] = handled_by

        if status in ("resolved", "ended"):
            update_data["ended_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(**update_data)
        )
        await self.db.commit()

        try:
            await mongo_log_service.write_conversation_event(
                conversation_id=str(conversation.id),
                event_type="status_changed",
                detail={"from": conversation.status if conversation else "unknown", "to": status},
            )
        except Exception:
            pass

        if status in ("resolved", "closed"):
            try:
                await mongo_log_service.archive_conversation_transcript(
                    conversation_id=str(conversation.id),
                    messages=[],
                    operation_logs=[],
                    events=[],
                )
            except Exception:
                pass

        await cache_service.delete(
            session_cache_key(session_id),
            chat_history_key(conversation.id),
        )

    async def get_conversation_by_id(
        self, conversation_id: str
    ) -> Conversation | None:
        """根据ID获取会话"""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_conversation_messages(
        self, conversation_id: str
    ) -> list[Message]:
        """获取会话的所有消息"""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())
