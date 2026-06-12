"""
API Keys Management API
模型配置管理模块
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_db, get_admin_user
from app.schemas.common import BaseResponse
from app.services.model_config_service import ModelConfigService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=BaseResponse)
async def get_model_configs(
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取模型配置列表"""
    service = ModelConfigService(db)
    configs = await service.get_configs()

    return BaseResponse(
        data=[
            {
                "id": config.id,
                "name": config.name,
                "baseUrl": config.base_url,
                "apiKey": service.mask_api_key("sk-xxxxxx"),
                "modelId": config.model_id,
                "status": config.status,
                "contextWindow": config.context_window,
                "agentsCount": len(config.agents),
                "createdAt": config.created_at.isoformat() if config.created_at else None,
            }
            for config in configs
        ]
    )


@router.post("", response_model=BaseResponse)
async def create_model_config(
    data: dict,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """创建模型配置"""
    service = ModelConfigService(db)
    config = await service.create_config(
        name=data["name"],
        base_url=data["baseUrl"],
        api_key=data["apiKey"],
        model_id=data["modelId"],
    )
    return BaseResponse(data={"id": config.id})


@router.put("/{config_id}", response_model=BaseResponse)
async def update_model_config(
    config_id: str,
    data: dict,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """更新模型配置"""
    service = ModelConfigService(db)
    await service.update_config(
        config_id=config_id,
        name=data.get("name"),
        base_url=data.get("baseUrl"),
        api_key=data.get("apiKey"),
        model_id=data.get("modelId"),
    )
    return BaseResponse(message="更新成功")


@router.delete("/{config_id}", response_model=BaseResponse)
async def delete_model_config(
    config_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """删除模型配置"""
    service = ModelConfigService(db)
    await service.delete_config(config_id)
    return BaseResponse(message="删除成功")


@router.post("/{config_id}/test", response_model=BaseResponse)
async def test_model_config(
    config_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """测试模型配置"""
    service = ModelConfigService(db)
    result = await service.test_config(config_id)
    return BaseResponse(data=result)
