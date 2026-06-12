"""
Dashboard API
仪表盘模块
"""

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_db, get_admin_user
from app.schemas.dashboard import (
    MetricsResponse,
    RealtimeStatusResponse,
    IntentDistributionResponse,
    ChannelDistributionResponse,
    RecentConversationsResponse,
)
from app.services.dashboard_service import DashboardService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    range: str = Query("today", description="时间范围：today/week/month"),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> MetricsResponse:
    """获取核心指标"""
    service = DashboardService(db)
    return await service.get_metrics(range_str=range)


@router.get("/realtime-status", response_model=RealtimeStatusResponse)
async def get_realtime_status(
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RealtimeStatusResponse:
    """获取实时对话状态"""
    service = DashboardService(db)
    return await service.get_realtime_status()


@router.get("/intent-distribution", response_model=IntentDistributionResponse)
async def get_intent_distribution(
    range: str = Query("today", description="时间范围：today/week/month"),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> IntentDistributionResponse:
    """获取意图分布"""
    service = DashboardService(db)
    return await service.get_intent_distribution(range_str=range)


@router.get("/channel-distribution", response_model=ChannelDistributionResponse)
async def get_channel_distribution(
    range: str = Query("today", description="时间范围：today/week/month"),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ChannelDistributionResponse:
    """获取渠道分布"""
    service = DashboardService(db)
    return await service.get_channel_distribution(range_str=range)


@router.get("/recent-conversations", response_model=RecentConversationsResponse)
async def get_recent_conversations(
    limit: int = Query(10, ge=1, le=50),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RecentConversationsResponse:
    """获取最近对话列表"""
    service = DashboardService(db)
    conversations = await service.get_recent_conversations(limit=limit)
    return RecentConversationsResponse(data=conversations)
