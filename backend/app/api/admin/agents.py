"""
Agents API
Agent管理模块
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.core.exceptions import AgentNotFoundError
from app.dependencies import get_db, get_admin_user
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentDetail,
    AgentListItem,
    MCPServerLinkRequest,
    ToolToggleRequest,
)
from app.schemas.common import BaseResponse, PaginatedResponse
from app.services.agent_service import AgentService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=BaseResponse)
async def get_agents(
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取Agent列表"""
    service = AgentService(db)
    agents = await service.get_agents()
    return BaseResponse(data=agents)


@router.post("", response_model=BaseResponse)
async def create_agent(
    data: AgentCreate,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """创建Agent"""
    service = AgentService(db)
    agent = await service.create_agent(data)
    return BaseResponse(data={"id": agent.id})


@router.get("/{agent_id}", response_model=BaseResponse)
async def get_agent(
    agent_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取Agent详情"""
    service = AgentService(db)
    try:
        detail = await service.get_agent_detail(agent_id)
        return BaseResponse(data=detail.model_dump())
    except AgentNotFoundError:
        raise HTTPException(status_code=404, detail="Agent不存在")
    except Exception:
        logger.exception("获取Agent详情失败")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.put("/{agent_id}", response_model=BaseResponse)
async def update_agent(
    agent_id: str,
    data: AgentUpdate,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """更新Agent配置"""
    service = AgentService(db)
    await service.update_agent(agent_id, data)
    return BaseResponse(message="更新成功")


@router.patch("/{agent_id}/toggle", response_model=BaseResponse)
async def toggle_agent(
    agent_id: str,
    is_enabled: bool = Body(..., embed=True),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """切换Agent启用/禁用"""
    service = AgentService(db)
    await service.toggle_agent(agent_id, is_enabled)
    return BaseResponse(message="操作成功")


@router.post("/{agent_id}/skills/{skill_id}", response_model=BaseResponse)
async def assign_skill(
    agent_id: str,
    skill_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """分配Skill"""
    service = AgentService(db)
    await service.assign_skill(agent_id, skill_id)
    return BaseResponse(message="分配成功")


@router.delete("/{agent_id}/skills/{skill_id}", response_model=BaseResponse)
async def remove_skill(
    agent_id: str,
    skill_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """移除Skill"""
    service = AgentService(db)
    await service.remove_skill(agent_id, skill_id)
    return BaseResponse(message="移除成功")


@router.post("/{agent_id}/mcp-servers", response_model=BaseResponse)
async def link_mcp_server(
    agent_id: str,
    data: MCPServerLinkRequest,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """连接MCP Server"""
    service = AgentService(db)
    await service.link_mcp_server(agent_id, data.mcp_server_id, data.is_linked)
    return BaseResponse(message="连接成功")


@router.delete("/{agent_id}/mcp-servers/{mcp_server_id}", response_model=BaseResponse)
async def unlink_mcp_server(
    agent_id: str,
    mcp_server_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """断开MCP Server"""
    service = AgentService(db)
    await service.unlink_mcp_server(agent_id, mcp_server_id)
    return BaseResponse(message="断开成功")


@router.patch("/{agent_id}/tools/{tool_id}", response_model=BaseResponse)
async def toggle_tool(
    agent_id: str,
    tool_id: str,
    data: ToolToggleRequest,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """启用/禁用Agent工具"""
    service = AgentService(db)
    await service.toggle_tool(agent_id, tool_id, data.is_enabled)
    return BaseResponse(message="操作成功")


@router.delete("/{agent_id}", response_model=BaseResponse)
async def delete_agent(
    agent_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """删除Agent（软删除）"""
    service = AgentService(db)
    await service.delete_agent(agent_id)
    return BaseResponse(message="删除成功")


@router.post("/{agent_id}/sub-agents/{sub_agent_id}")
async def add_sub_agent(agent_id: str, sub_agent_id: str, admin_user: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    service = AgentService(db)
    await service.add_sub_agent(agent_id, sub_agent_id)
    return BaseResponse(message="添加成功")


@router.delete("/{agent_id}/sub-agents/{sub_agent_id}")
async def remove_sub_agent(agent_id: str, sub_agent_id: str, admin_user: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    service = AgentService(db)
    await service.remove_sub_agent(agent_id, sub_agent_id)
    return BaseResponse(message="移除成功")


@router.post("/{agent_id}/knowledge-documents/{document_id}")
async def add_knowledge_document(agent_id: str, document_id: str, admin_user: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    service = AgentService(db)
    await service.add_knowledge_document(agent_id, document_id)
    return BaseResponse(message="添加成功")


@router.delete("/{agent_id}/knowledge-documents/{document_id}")
async def remove_knowledge_document(agent_id: str, document_id: str, admin_user: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    service = AgentService(db)
    await service.remove_knowledge_document(agent_id, document_id)
    return BaseResponse(message="移除成功")


@router.post("/{agent_id}/knowledge-qa/{qa_id}")
async def add_knowledge_qa(agent_id: str, qa_id: str, admin_user: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    service = AgentService(db)
    await service.add_knowledge_qa(agent_id, qa_id)
    return BaseResponse(message="添加成功")


@router.delete("/{agent_id}/knowledge-qa/{qa_id}")
async def remove_knowledge_qa(agent_id: str, qa_id: str, admin_user: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    service = AgentService(db)
    await service.remove_knowledge_qa(agent_id, qa_id)
    return BaseResponse(message="移除成功")


@router.get("/logs/operation-logs/{conversation_id}")
async def get_operation_logs(
    conversation_id: str,
    date: str | None = Query(None),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.agent_log_service import agent_log_service
    logs = await agent_log_service.query_logs(conversation_id, date)
    return BaseResponse(data=logs)
