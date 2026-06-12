"""
Skills API
技能管理模块
"""

import io
import logging
import zipfile

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_admin_user
from app.models.skill import Skill
from app.schemas.common import BaseResponse
from app.schemas.skill import SkillCreate, SkillUpdate
from app.services.skill_service import SkillService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=BaseResponse)
async def get_skills(
    category: str | None = Query(None),
    tags: str | None = Query(None, description="Comma-separated tag list"),
    status: str | None = Query(None),
    search: str | None = Query(None),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取Skills列表"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    service = SkillService(db)
    skills = await service.get_skills(
        category=category,
        tags=tag_list,
        status=status,
        search=search,
    )

    return BaseResponse(
        data=[
            {
                "id": s.id,
                "name": s.name,
                "displayName": s.display_name,
                "icon": s.icon,
                "iconColor": s.icon_color,
                "category": s.category,
                "description": s.description,
                "status": s.status,
                "skillBody": s.skill_body,
                "tags": s.tags,
                "version": s.version,
                "author": s.author,
                "prompts": s.prompts,
                "isBuiltin": s.is_builtin,
                "resources": [
                    {
                        "id": r.id,
                        "skillId": r.skill_id,
                        "fileName": r.file_name,
                        "filePath": r.file_path,
                        "fileSize": r.file_size,
                        "mimeType": r.mime_type,
                        "createdAt": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in s.resources
                ] if s.resources else [],
            }
            for s in skills
        ]
    )


@router.get("/tags", response_model=BaseResponse)
async def get_all_tags(
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取所有技能标签"""
    service = SkillService(db)
    tags = await service.get_all_tags()
    return BaseResponse(data=tags)


@router.post("", response_model=BaseResponse)
async def create_skill(
    data: SkillCreate,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """创建Skill"""
    service = SkillService(db)
    skill = await service.create_skill(data)
    return BaseResponse(data={"id": skill.id})


@router.put("/{skill_id}", response_model=BaseResponse)
async def update_skill(
    skill_id: str,
    data: SkillUpdate,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """更新Skill"""
    service = SkillService(db)
    await service.update_skill(skill_id, data)
    return BaseResponse(message="更新成功")


@router.delete("/{skill_id}", response_model=BaseResponse)
async def delete_skill(
    skill_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """删除Skill"""
    service = SkillService(db)
    await service.delete_skill(skill_id)
    return BaseResponse(message="删除成功")


@router.post("/{skill_id}/test", response_model=BaseResponse)
async def test_skill(
    skill_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """测试Skill执行（调用LLM获取真实响应）"""
    service = SkillService(db)
    result = await service.test_skill(skill_id)
    return BaseResponse(data=result)


@router.post("/import", response_model=BaseResponse)
async def import_skill(
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """导入Skill（zip 格式）"""
    service = SkillService(db)
    zip_content = await file.read()

    try:
        skill = await service.import_skill_from_zip(zip_content)
    except ValueError as e:
        error_msg = str(e)
        if "SKILL.md not found" in error_msg:
            raise HTTPException(status_code=400, detail="SKILL.md not found")
        if "Skill name already exists" in error_msg:
            raise HTTPException(status_code=409, detail="Skill name already exists")
        raise HTTPException(status_code=400, detail=error_msg)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="文件格式错误：仅支持 .zip 格式")
    except Exception as e:
        logger.error(f"导入skill失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导入失败：内部错误 - {str(e)}")

    return BaseResponse(data={"id": skill.id})


@router.get("/{skill_id}/export")
async def export_skill(
    skill_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """导出Skill为 zip 文件"""
    service = SkillService(db)
    zip_bytes = await service.export_skill_to_zip(skill_id)

    result = await db.execute(
        select(Skill.name).where(Skill.id == skill_id)
    )
    skill_name = result.scalar_one_or_none()
    filename = f"{skill_name}.zip" if skill_name else "skill.zip"

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
