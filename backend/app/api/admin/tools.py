"""
Tools API
工具管理模块
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_db, get_admin_user
from app.schemas.tool import (
    BuiltinToolResponse,
    BuiltinToolItem,
)
from app.schemas.common import BaseResponse
from app.models.tool import ToolConfig
from app.models.mcp_server import MCPServer
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/built-in", response_model=BuiltinToolResponse)
async def get_builtin_tools(
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BuiltinToolResponse:
    """获取内置工具列表"""
    result = await db.execute(
        select(ToolConfig).where(ToolConfig.is_builtin == True)
    )
    tools = result.scalars().all()

    return BuiltinToolResponse(
        data=[
            BuiltinToolItem(
                id=tool.id,
                name=tool.name,
                name_en=tool.name_en,
                icon=tool.icon,
                description=tool.description,
                category=tool.category,
                category_label=tool.category_label,
                category_icon=tool.category_icon,
                is_enabled=tool.is_enabled,
            )
            for tool in tools
        ]
    )


from app.schemas.agent import ToolToggleRequest

@router.patch("/built-in/{tool_id}", response_model=BaseResponse)
async def toggle_builtin_tool(
    tool_id: str,
    data: ToolToggleRequest,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """启用/禁用内置工具"""
    await db.execute(
        update(ToolConfig)
        .where(
            ToolConfig.id == tool_id,
            ToolConfig.is_builtin == True,
        )
        .values(is_enabled=data.is_enabled)
    )
    await db.commit()
    return BaseResponse(message="操作成功")


@router.get("", response_model=BaseResponse)
async def get_tools(
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取工具列表"""
    result = await db.execute(
        select(ToolConfig).where(ToolConfig.is_enabled == True)
    )
    tools = result.scalars().all()
    return BaseResponse(
        data=[
            {
                "id": tool.id,
                "name": tool.name,
                "nameEn": tool.name_en,
                "icon": tool.icon,
                "description": tool.description,
                "category": tool.category,
                "isBuiltin": tool.is_builtin,
                "toolType": tool.tool_type,
                "isEnabled": tool.is_enabled,
            }
            for tool in tools
        ]
    )


@router.get("/mcp", response_model=BaseResponse)
async def get_mcp_tools(
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取MCP工具列表，按server分组"""
    result = await db.execute(
        select(ToolConfig, MCPServer.name.label("server_name"), MCPServer.status.label("server_status"))
        .join(MCPServer, ToolConfig.mcp_server_id == MCPServer.id)
        .where(ToolConfig.tool_type == "mcp", MCPServer.is_enabled == True)
    )
    rows = result.all()

    grouped: dict[str, dict] = {}
    for tool, server_name, server_status in rows:
        server_id = tool.mcp_server_id
        if server_id not in grouped:
            grouped[server_id] = {
                "server_id": server_id,
                "server_name": server_name,
                "server_status": server_status,
                "tools": [],
            }
        grouped[server_id]["tools"].append({
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "is_enabled": tool.is_enabled,
        })

    return BaseResponse(data=list(grouped.values()))


@router.patch("/mcp/bulk-toggle", response_model=BaseResponse)
async def bulk_toggle_mcp_tools(
    data: dict,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """批量切换某MCP服务下所有工具状态"""
    server_id = data.get("server_id")
    is_enabled = data.get("is_enabled", True)
    await db.execute(
        update(ToolConfig)
        .where(ToolConfig.mcp_server_id == server_id, ToolConfig.tool_type == "mcp")
        .values(is_enabled=is_enabled)
    )
    await db.commit()
    return BaseResponse(data={"server_id": server_id, "is_enabled": is_enabled})


@router.patch("/mcp/{tool_id}", response_model=BaseResponse)
async def toggle_mcp_tool(
    tool_id: str,
    data: ToolToggleRequest,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """启用/禁用MCP工具"""
    await db.execute(
        update(ToolConfig)
        .where(
            ToolConfig.id == tool_id,
            ToolConfig.tool_type == "mcp",
        )
        .values(is_enabled=data.is_enabled)
    )
    await db.commit()

    result = await db.execute(
        select(ToolConfig).where(ToolConfig.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        return BaseResponse(code=404, message="工具不存在")

    return BaseResponse(data={
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "is_enabled": tool.is_enabled,
    })


@router.get("/{tool_id}", response_model=BaseResponse)
async def get_tool(
    tool_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取工具详情"""
    result = await db.execute(
        select(ToolConfig).where(ToolConfig.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        return BaseResponse(code=404, message="工具不存在")
    return BaseResponse(
        data={
            "id": tool.id,
            "name": tool.name,
            "nameEn": tool.name_en,
            "icon": tool.icon,
            "description": tool.description,
            "category": tool.category,
            "isBuiltin": tool.is_builtin,
            "isEnabled": tool.is_enabled,
        }
    )


@router.post("", response_model=BaseResponse)
async def create_tool(
    data: dict,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """创建自定义工具"""
    tool = ToolConfig(
        name=data["name"],
        name_en=data.get("nameEn", ""),
        icon=data.get("icon", "build"),
        description=data.get("description", ""),
        category=data.get("category", "custom"),
        category_label=data.get("categoryLabel", "自定义"),
        category_icon=data.get("categoryIcon", "build"),
        is_builtin=False,
        is_enabled=True,
    )
    db.add(tool)
    await db.commit()
    return BaseResponse(data={"id": tool.id})


@router.put("/{tool_id}", response_model=BaseResponse)
async def update_tool(
    tool_id: str,
    data: dict,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """更新工具"""
    update_data = {}
    if "name" in data:
        update_data["name"] = data["name"]
    if "nameEn" in data:
        update_data["name_en"] = data["nameEn"]
    if "icon" in data:
        update_data["icon"] = data["icon"]
    if "description" in data:
        update_data["description"] = data["description"]
    if "category" in data:
        update_data["category"] = data["category"]
    if update_data:
        await db.execute(
            update(ToolConfig)
            .where(ToolConfig.id == tool_id)
            .values(**update_data)
        )
        await db.commit()
    return BaseResponse(message="更新成功")


@router.delete("/{tool_id}", response_model=BaseResponse)
async def delete_tool(
    tool_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """删除工具"""
    await db.execute(
        delete(ToolConfig).where(ToolConfig.id == tool_id)
    )
    await db.commit()
    return BaseResponse(message="删除成功")


@router.post("/{tool_id}/test", response_model=BaseResponse)
async def test_tool(
    tool_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """测试工具"""
    result = await db.execute(
        select(ToolConfig).where(ToolConfig.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        return BaseResponse(code=404, message="工具不存在")
    return BaseResponse(
        data={
            "status": "success",
            "toolId": tool.id,
            "toolName": tool.name,
        }
    )
