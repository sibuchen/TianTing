"""
History API
历史记录模块
"""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, get_db
from app.schemas.conversation import HistoryListResponse, HistoryDetailResponse
from app.services.conversation_service import ConversationService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=HistoryListResponse)
async def get_history(
    search: str | None = Query(None),
    status: str | None = Query(None),
    intent: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HistoryListResponse:
    """获取历史对话列表"""
    from app.models.conversation import Conversation

    query = select(Conversation)

    if current_user.get("role") == "operator":
        from app.models.human_session import HumanSession

        operator_conversation_ids = select(HumanSession.conversation_id).where(
            HumanSession.operator_id == current_user["sub"]
        )
        query = query.where(Conversation.id.in_(operator_conversation_ids))

    if search:
        query = query.where(Conversation.user_name.ilike(f"%{search}%"))

    if status:
        query = query.where(Conversation.status == status)

    if intent:
        query = query.where(Conversation.intent == intent)

    if start_date:
        from datetime import datetime as dt

        query = query.where(Conversation.started_at >= dt.combine(start_date, dt.min.time()))

    if end_date:
        from datetime import datetime as dt

        query = query.where(Conversation.started_at <= dt.combine(end_date, dt.max.time()))

    from sqlalchemy import func, select as sa_select
    from sqlalchemy import column

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    query = query.order_by(Conversation.started_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    conversations = result.scalars().all()

    return HistoryListResponse(
        data={
            "items": [
                {
                    "id": conv.id,
                    "userName": conv.user_name,
                    "userId": conv.user_id,
                    "userAvatar": conv.user_avatar,
                    "intent": conv.intent,
                    "status": conv.status,
                    "channel": conv.channel,
                    "startedAt": conv.started_at.isoformat() if conv.started_at else None,
                    "endedAt": conv.ended_at.isoformat() if conv.ended_at else None,
                    "duration": 0,
                    "messageCount": conv.message_count,
                    "handledBy": conv.handled_by,
                    "preview": "",
                }
                for conv in conversations
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    )


@router.get("/{conversation_id}", response_model=HistoryDetailResponse)
async def get_conversation_detail(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HistoryDetailResponse:
    """获取对话详情"""
    service = ConversationService(db)
    conversation = await service.get_conversation_by_id(conversation_id)

    if not conversation:
        return HistoryDetailResponse(
            code=50001,
            data={
                "id": conversation_id,
                "userName": None,
                "userId": None,
                "userAvatar": None,
                "intent": None,
                "status": "not_found",
                "startedAt": None,
                "endedAt": None,
                "messages": [],
            },
        )

    if current_user.get("role") == "operator":
        from app.models.human_session import HumanSession

        session_result = await db.execute(
            select(HumanSession).where(
                HumanSession.conversation_id == conversation_id,
                HumanSession.operator_id == current_user["sub"],
            )
        )
        if not session_result.scalar_one_or_none():
            return HistoryDetailResponse(
                code=50001,
                data={
                    "id": conversation_id,
                    "userName": None,
                    "userId": None,
                    "userAvatar": None,
                    "intent": None,
                    "status": "not_found",
                    "startedAt": None,
                    "endedAt": None,
                    "messages": [],
                },
            )

    messages = await service.get_conversation_messages(conversation_id)

    return HistoryDetailResponse(
        data={
            "id": conversation.id,
            "userName": conversation.user_name,
            "userId": conversation.user_id,
            "userAvatar": conversation.user_avatar,
            "intent": conversation.intent,
            "status": conversation.status,
            "channel": conversation.channel,
            "startedAt": conversation.started_at.isoformat() if conversation.started_at else None,
            "endedAt": conversation.ended_at.isoformat() if conversation.ended_at else None,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                    "type": "text",
                    "agentName": msg.agent_name,
                    "toolCalls": msg.tool_calls,
                    "isSystemMessage": msg.is_system_message,
                }
                for msg in messages
            ],
        }
    )
