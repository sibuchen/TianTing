"""
Analytics Export API
数据导出 API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.analytics_export_service import AnalyticsExportService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/export/conversations")
async def export_conversations(db: AsyncSession = Depends(get_db)):
    service = AnalyticsExportService(db)
    filepath = await service.export_conversations()
    return {"status": "success", "file": filepath}


@router.get("/export/messages")
async def export_messages(db: AsyncSession = Depends(get_db)):
    service = AnalyticsExportService(db)
    filepath = await service.export_messages()
    return {"status": "success", "file": filepath}


@router.get("/export/agent-usage")
async def export_agent_usage(db: AsyncSession = Depends(get_db)):
    service = AnalyticsExportService(db)
    filepath = await service.export_agent_usage()
    return {"status": "success", "file": filepath}


@router.get("/export/all")
async def export_all(db: AsyncSession = Depends(get_db)):
    service = AnalyticsExportService(db)
    results = await service.export_all()
    return {"status": "success", "files": results}