"""
Messages API
消息收发+SSE流式响应
"""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.schemas.conversation import (
    MessageListResponse,
    ChatMessageRequest,
    ChatStatusResponse,
    FeedbackRequest,
)
from app.schemas.common import BaseResponse
from app.services.conversation_service import ConversationService
from app.agents.runtime.runtime import AgentRuntime
from app.dependencies import get_db
from app.ws.channels import channels
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def get_messages(
    session_id: str,
    before: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    """获取历史消息"""
    service = ConversationService(db)
    messages, has_more = await service.get_messages(session_id, before, limit)

    return MessageListResponse(
        data={
            "messages": [msg.model_dump() for msg in messages],
            "hasMore": has_more,
        }
    )


async def generate_chat_stream(
    session_id: str,
    content: str,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    service = ConversationService(db)

    await service.check_rate_limit(session_id)

    user_message = await service.add_message(
        session_id=session_id,
        role="user",
        content=content,
    )

    yield f"event: message\ndata: {json.dumps({'type': 'message', 'id': user_message.id})}\n\n"

    conversation, _ = await service.get_session(session_id)

    runtime = AgentRuntime(db)

    is_transfer = False
    full_response = ""

    async for chunk in runtime.process_message_stream(
        conversation_id=conversation.id,
        user_content=content,
        channel="web",
    ):
        if chunk == "__TRANSFER_TO_HUMAN__":
            is_transfer = True
            break
        full_response += chunk
        yield f"event: message\ndata: {json.dumps({'type': 'assistant', 'content': chunk})}\n\n"

    if is_transfer:
        transfer_notice = "正在为您转接人工客服，请稍候..."
        await service.add_message(
            session_id=session_id,
            role="system",
            content=transfer_notice,
            is_system_message=True,
        )
        yield f"event: message\ndata: {json.dumps({'type': 'assistant', 'content': transfer_notice})}\n\n"

        from app.services.human_service import HumanService
        human_service = HumanService(db)
        await human_service.transfer_to_human(conversation.id)

        await channels.publish_new_conversation({
            "id": conversation.id,
            "userName": conversation.user_name,
            "userId": conversation.user_id,
            "intent": conversation.intent,
            "status": "transferred",
            "channel": "web",
        })
    else:
        await service.add_message(
            session_id=session_id,
            role="agent",
            content=full_response,
        )

    yield f"event: done\ndata: {json.dumps({'type': 'done'})}\n\n"


@router.post("/{session_id}/messages")
async def send_message(
    session_id: str,
    data: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """发送消息（SSE流式响应）"""
    return StreamingResponse(
        generate_chat_stream(session_id, data.content, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{session_id}/status", response_model=BaseResponse)
async def get_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取会话状态"""
    service = ConversationService(db)
    info = await service.get_session_info(session_id)

    return BaseResponse(
        data={
            "status": info.status,
            "handledBy": info.handled_by,
            "agentName": None,
        }
    )


@router.post("/{session_id}/feedback", response_model=BaseResponse)
async def submit_feedback(
    session_id: str,
    data: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """消息反馈"""
    return BaseResponse(message="反馈已提交")
