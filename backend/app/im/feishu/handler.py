import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.services.conversation_service import ConversationService
from app.agents.runtime.runtime import AgentRuntime
from app.im.feishu.client import get_feishu_client
from app.ws.channels import channels

logger = logging.getLogger(__name__)


async def handle_feishu_message(
    open_id: str,
    chat_id: str,
    message_text: str,
    message_id: str | None = None,
    db: AsyncSession = None,
) -> None:
    feishu_client = get_feishu_client()

    conversation = await _find_or_create_conversation(
        open_id=open_id,
        chat_id=chat_id,
        db=db,
    )

    service = ConversationService(db)

    user_message = await service.add_message(
        session_id=conversation.session_id,
        role="user",
        content=message_text,
    )

    await _broadcast_user_message(conversation, user_message)

    agent_response_text = await _invoke_agent(
        conversation=conversation,
        user_content=message_text,
        db=db,
    )

    if agent_response_text == "__TRANSFER_TO_HUMAN__":
        from app.services.human_service import HumanService
        human_service = HumanService(db)
        await human_service.transfer_to_human(conversation.id)

        transfer_notice = "您好，正在为您转接人工客服，请稍候..."
        await service.add_message(
            session_id=conversation.session_id,
            role="system",
            content=transfer_notice,
            is_system_message=True,
        )
        await feishu_client.send_message(open_id, transfer_notice)

        await channels.publish_conversation_update(
            conversation.id,
            {"status": "transferred", "handledBy": "human"},
        )
    else:
        agent_message = await service.add_message(
            session_id=conversation.session_id,
            role="agent",
            content=agent_response_text,
        )

        await _broadcast_agent_message(conversation, agent_message)

        await feishu_client.send_message(open_id, agent_response_text)


async def _find_or_create_conversation(
    open_id: str,
    chat_id: str,
    db: AsyncSession,
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            and_(
                Conversation.channel == "feishu",
                Conversation.feishu_open_id == open_id,
                Conversation.status.in_(["active", "transferred"]),
            )
        )
    )
    conversation = result.scalar_one_or_none()

    if conversation:
        return conversation

    feishu_client = get_feishu_client()
    user_name = await feishu_client.get_user_name(open_id)
    if not user_name:
        user_name = f"飞书用户_{open_id[:8]}"

    session_id = str(uuid.uuid4())
    service = ConversationService(db)
    session_resp = await service.create_session(
        session_id=session_id,
        user_id=f"feishu:{open_id}",
        user_name=user_name,
        channel="feishu",
    )

    result = await db.execute(
        select(Conversation).where(Conversation.id == session_resp.conversation_id)
    )
    conversation = result.scalar_one()

    conversation.feishu_open_id = open_id
    conversation.feishu_chat_id = chat_id
    await db.commit()
    await db.refresh(conversation)

    await channels.publish_new_conversation({
        "id": conversation.id,
        "userName": conversation.user_name,
        "userId": conversation.user_id,
        "intent": conversation.intent,
        "status": conversation.status,
        "channel": "feishu",
        "startedAt": conversation.started_at.isoformat() if conversation.started_at else None,
    })

    return conversation


async def _invoke_agent(
    conversation: Conversation,
    user_content: str,
    db: AsyncSession,
) -> str:
    try:
        logger.debug(f"[_invoke_agent] Creating AgentRuntime for conversation {conversation.id}")
        runtime = AgentRuntime(db)
        logger.debug("[_invoke_agent] Calling process_message...")
        response = await runtime.process_message(
            conversation_id=conversation.id,
            user_content=user_content,
            channel="feishu",
        )
        logger.debug(f"[_invoke_agent] process_message returned: {response[:100] if response else 'None'}")
        return response
    except Exception as e:
        logger.error(f"Agent invocation error: {e}", exc_info=True)
        return "抱歉，系统暂时无法处理您的消息，请稍后再试。"


async def _broadcast_user_message(
    conversation: Conversation, message: Message
) -> None:
    await channels.publish_message(conversation.session_id, {
        "id": message.id,
        "role": "user",
        "content": message.content,
        "timestamp": message.created_at.isoformat() if message.created_at else None,
    })


async def _broadcast_agent_message(
    conversation: Conversation, message: Message
) -> None:
    await channels.publish_message(conversation.session_id, {
        "id": message.id,
        "role": "agent",
        "content": message.content,
        "timestamp": message.created_at.isoformat() if message.created_at else None,
    })
