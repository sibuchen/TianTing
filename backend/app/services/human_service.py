"""
Human Service
人工客服服务：转接/排队/分配
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConversationNotFoundError,
    NotTransferredToHumanError,
    ConversationAlreadyTakenError,
    HumanServiceEndedError,
)
from app.models.conversation import Conversation
from app.im.feishu.client import get_feishu_client
from app.models.human_session import HumanSession
from app.models.quick_reply import QuickReply
from app.models.message import Message
from app.schemas.human_service import QueueItem


class HumanService:
    """人工客服服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_queue(self, operator_id: str | None = None) -> list[QueueItem]:
        """获取等待队列（含当前 operator 的活跃对话）"""
        waiting_result = await self.db.execute(
            select(HumanSession)
            .options()
            .where(
                HumanSession.status == "waiting",
            )
            .order_by(HumanSession.created_at.asc())
        )
        waiting_sessions = list(waiting_result.scalars().all())

        active_sessions: list[HumanSession] = []
        if operator_id:
            active_result = await self.db.execute(
                select(HumanSession)
                .options()
                .where(
                    HumanSession.status == "active",
                    HumanSession.operator_id == operator_id,
                )
                .order_by(HumanSession.started_at.asc())
            )
            active_sessions = list(active_result.scalars().all())

        all_sessions = waiting_sessions + active_sessions

        queue_items = []
        for session in all_sessions:
            conv_result = await self.db.execute(
                select(Conversation).where(Conversation.id == session.conversation_id)
            )
            conversation = conv_result.scalar_one_or_none()

            if conversation:
                if session.status == "active" and session.started_at:
                    waiting_duration = int(
                        (datetime.now(timezone.utc) - session.started_at).total_seconds()
                    )
                else:
                    waiting_duration = int(
                        (datetime.now(timezone.utc) - session.created_at).total_seconds()
                    )

                last_message = None
                msg_result = await self.db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.desc())
                    .limit(1)
                )
                last_msg = msg_result.scalar_one_or_none()
                if last_msg:
                    last_message = {
                        "content": last_msg.content[:50],
                        "role": last_msg.role,
                        "timestamp": last_msg.created_at.isoformat() if last_msg.created_at else None,
                    }

                queue_items.append(
                    QueueItem(
                        conversation_id=conversation.id,
                        user_id=conversation.user_id,
                        user_name=conversation.user_name,
                        user_avatar=conversation.user_avatar,
                        intent=conversation.intent,
                        channel=conversation.channel,
                        waiting_duration=waiting_duration,
                        status=session.status,
                        last_message=last_message,
                    )
                )

        return queue_items

    async def accept_conversation(
        self, conversation_id: str, operator_id: str
    ) -> None:
        """接手对话"""
        conv_result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
            )
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            raise ConversationNotFoundError()

        if conversation.status != "transferred":
            raise NotTransferredToHumanError()

        session_result = await self.db.execute(
            select(HumanSession).where(
                HumanSession.conversation_id == conversation_id,
            )
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise NotTransferredToHumanError()

        if session.status != "waiting":
            raise ConversationAlreadyTakenError()

        if session.operator_id and session.operator_id != operator_id:
            raise ConversationAlreadyTakenError()

        await self.db.execute(
            update(HumanSession)
            .where(HumanSession.id == session.id)
            .values(
                status="active",
                operator_id=operator_id,
                started_at=datetime.now(timezone.utc),
            )
        )

        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                handled_by="human",
                status="active",
            )
        )

        await self.db.commit()

    async def get_session_messages(
        self,
        conversation_id: str,
        before: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Message], bool]:
        """获取会话消息"""
        query = select(Message).where(
            Message.conversation_id == conversation_id,
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
        messages = list(result.scalars().all())
        messages.reverse()

        has_more = len(messages) == limit

        return messages, has_more

    async def send_message(
        self, conversation_id: str, operator_id: str, content: str
    ) -> Message:
        """客服发送消息"""
        session_result = await self.db.execute(
            select(HumanSession).where(
                HumanSession.conversation_id == conversation_id,
            )
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise NotTransferredToHumanError()

        if session.status == "ended":
            raise HumanServiceEndedError()

        message = Message(
            conversation_id=conversation_id,
            role="human_agent",
            content=content,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if conversation and conversation.channel == "feishu" and conversation.feishu_open_id:
            feishu_client = get_feishu_client()
            await feishu_client.send_message(conversation.feishu_open_id, content)

        return message

    async def end_session(self, conversation_id: str, operator_id: str) -> None:
        """结束人工服务"""
        session_result = await self.db.execute(
            select(HumanSession).where(
                HumanSession.conversation_id == conversation_id,
            )
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise NotTransferredToHumanError()

        if session.status == "ended":
            raise HumanServiceEndedError()

        await self.db.execute(
            update(HumanSession)
            .where(HumanSession.id == session.id)
            .values(
                status="ended",
                ended_at=datetime.now(timezone.utc),
            )
        )

        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                status="resolved",
                handled_by="agent",
                ended_at=datetime.now(timezone.utc),
            )
        )

        await self.db.commit()

        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if conversation and conversation.channel == "feishu" and conversation.feishu_open_id:
            feishu_client = get_feishu_client()
            await feishu_client.send_message(
                conversation.feishu_open_id,
                "人工服务已结束，感谢您的咨询。如有其他问题，欢迎随时联系！",
            )

    async def get_quick_replies(self) -> list[QuickReply]:
        """获取快捷回复列表"""
        result = await self.db.execute(
            select(QuickReply)
            .order_by(QuickReply.sort_order.asc())
        )
        return list(result.scalars().all())

    async def transfer_to_human(
        self, conversation_id: str, agent_id: str | None = None
    ) -> HumanSession:
        """转人工"""
        session = HumanSession(
            conversation_id=conversation_id,
            agent_id=agent_id,
            status="waiting",
        )
        self.db.add(session)

        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(status="transferred", handled_by="human")
        )

        await self.db.commit()
        await self.db.refresh(session)

        return session
