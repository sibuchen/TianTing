"""
Human Service API
人工客服模块
"""

from fastapi import APIRouter, Depends

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_current_user_optional, get_db
from app.models.human_session import HumanSession
from app.schemas.human_service import (
    QueueResponse,
    HumanSessionMessagesResponse,
    SendMessageRequest,
    SendMessageResponse,
    QuickReplyResponse,
)
from app.schemas.common import BaseResponse
from app.services.human_service import HumanService

router = APIRouter()


@router.get("/queue", response_model=QueueResponse)
async def get_queue(
    current_user: dict | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> QueueResponse:
    """获取等待队列"""
    service = HumanService(db)
    operator_id = current_user["sub"] if current_user else None
    queue = await service.get_queue(operator_id=operator_id)
    return QueueResponse(data=queue)


@router.post("/conversations/{conversation_id}/accept", response_model=BaseResponse)
async def accept_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """接手对话"""
    service = HumanService(db)
    await service.accept_conversation(conversation_id, current_user["sub"])
    return BaseResponse(message="接手成功")


@router.get("/conversations/{conversation_id}/messages", response_model=BaseResponse)
async def get_conversation_messages(
    conversation_id: str,
    before: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取对话消息"""
    service = HumanService(db)
    messages, has_more = await service.get_session_messages(
        conversation_id, before, limit
    )
    return BaseResponse(
        data={
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in messages
            ],
            "hasMore": has_more,
        }
    )


@router.post("/conversations/{conversation_id}/messages", response_model=BaseResponse)
async def send_message(
    conversation_id: str,
    data: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """客服发送消息"""
    service = HumanService(db)
    message = await service.send_message(
        conversation_id, current_user["sub"], data.content
    )
    return BaseResponse(
        data=SendMessageResponse(
            id=message.id,
            content=message.content,
            timestamp=message.created_at.isoformat() if message.created_at else None,
        ).model_dump()
    )


@router.post("/conversations/{conversation_id}/end", response_model=BaseResponse)
async def end_session(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """结束人工服务"""
    service = HumanService(db)
    await service.end_session(conversation_id, current_user["sub"])
    return BaseResponse(message="已结束人工服务")


@router.get("/quick-replies", response_model=QuickReplyResponse)
async def get_quick_replies(
    db: AsyncSession = Depends(get_db),
) -> QuickReplyResponse:
    """获取快捷回复列表"""
    service = HumanService(db)
    replies = await service.get_quick_replies()
    return QuickReplyResponse(
        data=[
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
            }
            for r in replies
        ]
    )


@router.get("/sessions", response_model=BaseResponse)
async def get_sessions(
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取人工客服会话列表"""
    result = await db.execute(
        select(HumanSession)
    )
    sessions = result.scalars().all()
    return BaseResponse(
        data=[
            {
                "id": s.id,
                "conversationId": s.conversation_id,
                "status": s.status,
                "operatorId": s.operator_id,
                "createdAt": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ]
    )


@router.get("/sessions/{session_id}", response_model=BaseResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取会话详情"""
    result = await db.execute(
        select(HumanSession).where(HumanSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return BaseResponse(code=404, message="会话不存在")
    return BaseResponse(
        data={
            "id": session.id,
            "conversationId": session.conversation_id,
            "status": session.status,
            "operatorId": session.operator_id,
            "startedAt": session.started_at.isoformat() if session.started_at else None,
            "endedAt": session.ended_at.isoformat() if session.ended_at else None,
            "createdAt": session.created_at.isoformat() if session.created_at else None,
        }
    )


@router.post("/sessions/{session_id}/assign", response_model=BaseResponse)
async def assign_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """分配会话给客服"""
    result = await db.execute(
        select(HumanSession).where(HumanSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return BaseResponse(code=404, message="会话不存在")
    service = HumanService(db)
    await service.accept_conversation(session.conversation_id, current_user["sub"])
    return BaseResponse(message="分配成功")


@router.post("/sessions/{session_id}/close", response_model=BaseResponse)
async def close_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """关闭会话"""
    result = await db.execute(
        select(HumanSession).where(HumanSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return BaseResponse(code=404, message="会话不存在")
    service = HumanService(db)
    await service.end_session(session.conversation_id, current_user["sub"])
    return BaseResponse(message="已关闭会话")
