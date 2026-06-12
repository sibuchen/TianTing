"""
Sessions API
聊天会话管理
"""

from fastapi import APIRouter, Depends

from app.schemas.conversation import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionInfoResponse,
)
from app.schemas.common import BaseResponse
from app.services.conversation_service import ConversationService
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("", response_model=SessionCreateResponse)
async def create_session(
    data: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionCreateResponse:
    """创建聊天会话"""
    service = ConversationService(db)
    return await service.create_session(
        user_id=data.user_id,
        user_name=data.user_name,
        user_avatar=data.user_avatar,
    )


@router.get("/{session_id}", response_model=BaseResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取会话信息"""
    service = ConversationService(db)
    info = await service.get_session_info(session_id)
    return BaseResponse(data=info.model_dump())
