"""
Settings API
系统设置模块
"""

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy import select, update, delete
import time
import asyncio
import os

from app.dependencies import get_current_user, get_db
from app.schemas.settings import (
    SettingsResponse,
    SettingsUpdateRequest,
    AvatarUploadResponse,
    PasswordChangeRequest,
    UpdateCheckResponse,
)
from app.schemas.common import BaseResponse
from app.services.settings_service import SettingsService
from app.services.auth_service import AuthService
from app.services.model_config_service import ModelConfigService
from app.models.mcp_server import MCPServer
from app.models.agent import AgentMCPServer
from app.schemas.tool import MCPServerCreate, MCPServerUpdate
from app.models.tool import ToolConfig
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    """获取系统设置"""
    from app.models.user import User

    result = await db.execute(
        select(User).where(User.id == current_user["sub"])
    )
    user = result.scalar_one_or_none()

    if not user:
        return SettingsResponse(code=1, message="用户不存在", data={})

    service = SettingsService(db)
    settings_data = await service.get_settings(user)

    return SettingsResponse(data=settings_data)


@router.put("", response_model=BaseResponse)
async def update_settings(
    data: SettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """更新系统设置"""
    service = SettingsService(db)

    appearance_data = data.appearance.model_dump(exclude_unset=True) if data.appearance else None
    notifications_data = data.notifications.model_dump(exclude_unset=True) if data.notifications else None
    chat_widget_data = data.chat_widget.model_dump(exclude_unset=True) if data.chat_widget else None

    await service.update_settings(
        appearance=appearance_data,
        notifications=notifications_data,
        chat_widget=chat_widget_data,
    )

    return BaseResponse(message="更新成功")


@router.post("/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvatarUploadResponse:
    """上传头像"""
    service = SettingsService(db)
    content = await file.read()
    avatar_url = await service.upload_avatar(
        current_user["sub"],
        content,
        file.filename or "avatar",
    )
    return AvatarUploadResponse(
        data={"avatar": avatar_url}
    )


@router.put("/password", response_model=BaseResponse)
async def change_password(
    data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """修改密码"""
    service = AuthService(db)
    await service.change_password(
        user_id=current_user["sub"],
        current_password=data.current_password,
        new_password=data.new_password,
        confirm_password=data.confirm_password,
    )
    return BaseResponse(message="密码修改成功")


@router.post("/check-update", response_model=UpdateCheckResponse)
async def check_update(
    db: AsyncSession = Depends(get_db),
) -> UpdateCheckResponse:
    """检查系统更新"""
    service = SettingsService(db)
    result = await service.check_update()
    return UpdateCheckResponse(data=result)


@router.get("/model-configs", response_model=BaseResponse)
async def get_model_configs(
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
                "provider": config.name,
                "baseUrl": config.base_url,
                "apiKey": service.mask_api_key("sk-xxxxxx"),
                "modelId": config.model_id,
                "capabilities": config.capabilities if config.capabilities else [config.model_id],
                "status": config.status,
                "contextWindow": config.context_window,
                "agentsCount": len(config.agents),
                "createdAt": config.created_at.isoformat() if config.created_at else None,
            }
            for config in configs
        ]
    )


@router.post("/model-configs", response_model=BaseResponse)
async def create_model_config(
    data: dict,
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


@router.put("/model-configs/{config_id}", response_model=BaseResponse)
async def update_model_config(
    config_id: str,
    data: dict,
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


@router.delete("/model-configs/{config_id}", response_model=BaseResponse)
async def delete_model_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """删除模型配置"""
    service = ModelConfigService(db)
    await service.delete_config(config_id)
    return BaseResponse(message="删除成功")


@router.post("/model-configs/{config_id}/test", response_model=BaseResponse)
async def test_model_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """测试模型配置"""
    service = ModelConfigService(db)
    result = await service.test_config(config_id)
    return BaseResponse(data=result)


@router.get("/mcp-servers", response_model=BaseResponse)
async def get_mcp_servers(
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取MCP Server列表"""
    result = await db.execute(
        select(MCPServer)
    )
    servers = result.scalars().all()
    return BaseResponse(
        data=[
            {
                "id": s.id,
                "name": s.name,
                "transportType": s.transport_type,
                "url": str(s.url) if s.url else None,
                "command": s.command,
                "args": s.args,
                "env": s.env,
                "status": s.status,
                "isEnabled": s.is_enabled,
                "toolsCount": len(s.tools or []),
            }
            for s in servers
        ]
    )


@router.post("/mcp-servers", response_model=BaseResponse)
async def create_mcp_server(
    data: MCPServerCreate,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """创建MCP Server"""
    server = MCPServer(
        name=data.name,
        transport_type=data.transport_type,
        url=str(data.url) if data.url else None,
        command=data.command,
        args=data.args,
        env=data.env,
        status="offline",
        is_enabled=True,
    )
    db.add(server)
    await db.commit()
    return BaseResponse(data={"id": server.id})


@router.put("/mcp-servers/{server_id}", response_model=BaseResponse)
async def update_mcp_server(
    server_id: str,
    data: MCPServerUpdate,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """更新MCP Server"""
    update_data = {}
    if data.name:
        update_data["name"] = data.name
    if data.transport_type:
        update_data["transport_type"] = data.transport_type
    if data.url:
        update_data["url"] = str(data.url)
    if data.command:
        update_data["command"] = data.command
    if data.args is not None:
        update_data["args"] = data.args
    if data.env is not None:
        update_data["env"] = data.env
    await db.execute(
        update(MCPServer)
        .where(MCPServer.id == server_id)
        .values(**update_data)
    )
    await db.commit()
    return BaseResponse(message="更新成功")


@router.delete("/mcp-servers/{server_id}", response_model=BaseResponse)
async def delete_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """删除MCP Server"""
    await db.execute(
        delete(MCPServer).where(MCPServer.id == server_id)
    )
    await db.execute(
        AgentMCPServer.__table__.delete().where(AgentMCPServer.mcp_server_id == server_id)
    )
    await db.execute(
        delete(ToolConfig).where(ToolConfig.mcp_server_id == server_id)
    )
    await db.commit()
    return BaseResponse(message="删除成功")


@router.post("/mcp-servers/{server_id}/test", response_model=BaseResponse)
async def test_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """测试MCP Server连接"""
    result = await db.execute(
        select(MCPServer).where(MCPServer.id == server_id)
    )
    server = result.scalar_one_or_none()
    if not server:
        return BaseResponse(code=30003, message="MCP Server不存在")

    start_time = time.time()
    transport_type = server.transport_type or "sse"

    try:
        if transport_type == "sse" and server.url:
            status, latency, tools_count, error, tools_list = await _test_sse_server(str(server.url))
        elif transport_type == "stdio" and server.command:
            status, latency, tools_count, error, tools_list = await _test_stdio_server(
                server.command, server.args or [], server.env or {}
            )
        else:
            return BaseResponse(code=30002, message="MCP Server配置不完整")

        await db.execute(
            update(MCPServer).where(MCPServer.id == server_id).values(status=status)
        )
        await db.commit()

        if status == "online" and tools_count > 0 and tools_list:
            result = await db.execute(
                select(ToolConfig).where(
                    ToolConfig.mcp_server_id == server_id,
                    ToolConfig.tool_type == "mcp",
                )
            )
            existing_tools: dict[str, ToolConfig] = {}
            for t in result.scalars().all():
                existing_tools[t.name] = t

            discovered_tool_names: set[str] = set()
            for tool_data in tools_list:
                tool_name = tool_data.get("name", "")
                if not tool_name:
                    continue
                discovered_tool_names.add(tool_name)

                if tool_name in existing_tools:
                    existing = existing_tools[tool_name]
                    await db.execute(
                        update(ToolConfig)
                        .where(ToolConfig.id == existing.id)
                        .values(
                            name=tool_name,
                            description=tool_data.get("description"),
                        )
                    )
                else:
                    new_tool = ToolConfig(
                        name=tool_name,
                        description=tool_data.get("description"),
                        tool_type="mcp",
                        mcp_server_id=server_id,
                        is_builtin=False,
                        is_enabled=True,
                        category="mcp",
                        category_label="MCP",
                    )
                    db.add(new_tool)

            for name, tool in existing_tools.items():
                if name not in discovered_tool_names:
                    await db.execute(
                        update(ToolConfig)
                        .where(ToolConfig.id == tool.id)
                        .values(is_enabled=False)
                    )

            await db.commit()

        data: dict = {
            "status": status,
            "latency": latency,
            "toolsCount": tools_count,
        }
        if error:
            data["error"] = error

        return BaseResponse(data=data)

    except Exception as e:
        await db.execute(
            update(MCPServer).where(MCPServer.id == server_id).values(status="offline")
        )
        await db.commit()
        return BaseResponse(
            data={
                "status": "offline",
                "latency": int((time.time() - start_time) * 1000),
                "toolsCount": 0,
                "error": str(e),
            }
        )


@router.patch("/mcp-servers/{server_id}/toggle", response_model=BaseResponse)
async def toggle_mcp_server(
    server_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """启用/禁用MCP Server，同时级联更新该服务下所有工具的启用状态"""
    is_enabled = data.get("is_enabled", True)
    await db.execute(
        update(MCPServer)
        .where(MCPServer.id == server_id)
        .values(is_enabled=is_enabled)
    )
    await db.execute(
        update(ToolConfig)
        .where(ToolConfig.mcp_server_id == server_id, ToolConfig.tool_type == "mcp")
        .values(is_enabled=is_enabled)
    )
    await db.commit()
    return BaseResponse(data={"id": server_id, "is_enabled": is_enabled})


async def _test_sse_server(url: str) -> tuple[str, int, int, str | None, list[dict]]:
    """测试SSE模式MCP Server"""
    import httpx

    start_time = time.time()
    error = None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            latency = int((time.time() - start_time) * 1000)

            if response.status_code < 500:
                return "online", latency, 0, None, []
            else:
                error = f"HTTP {response.status_code}"
                return "offline", latency, 0, error, []
    except httpx.ConnectError as e:
        latency = int((time.time() - start_time) * 1000)
        error = f"连接失败: {str(e)}"
        return "offline", latency, 0, error, []
    except httpx.TimeoutException:
        latency = int((time.time() - start_time) * 1000)
        error = "连接超时"
        return "offline", latency, 0, error, []
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        error = str(e)
        return "offline", latency, 0, error, []


async def _test_stdio_server(
    command: str, args: list, env_vars: dict
) -> tuple[str, int, int, str | None, list[dict]]:
    """测试stdio模式MCP Server（发送initialize握手）"""
    import json

    start_time = time.time()
    error = None
    tools_count = 0
    tools_list: list[dict] = []

    proc_env = {**os.environ, **env_vars}
    process = None

    try:
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=proc_env,
        )

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "tianting-test", "version": "1.0.0"},
            },
        }
        message = json.dumps(init_request) + "\n"

        process.stdin.write(message.encode())
        await process.stdin.drain()

        try:
            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=10.0
            )
            latency = int((time.time() - start_time) * 1000)

            response = json.loads(response_line.decode().strip())

            if "result" in response:
                result_data = response["result"]
                server_info = result_data.get("serverInfo", {})
                capabilities = result_data.get("capabilities", {})
                if capabilities.get("tools"):
                    tools_count = -1

                try:
                    initialized_notification = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                    }
                    notification_msg = json.dumps(initialized_notification) + "\n"
                    process.stdin.write(notification_msg.encode())
                    await process.stdin.drain()

                    if tools_count == -1:
                        tools_request = {
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/list",
                            "params": {},
                        }
                        tools_msg = json.dumps(tools_request) + "\n"
                        process.stdin.write(tools_msg.encode())
                        await process.stdin.drain()

                        tools_line = await asyncio.wait_for(
                            process.stdout.readline(), timeout=5.0
                        )
                        tools_response = json.loads(tools_line.decode().strip())
                        tools_list = tools_response.get("result", {}).get("tools", [])
                        tools_count = len(tools_list)
                except Exception:
                    if tools_count == -1:
                        tools_count = 0

                return "online", latency, tools_count, None, tools_list
            else:
                error_msg = response.get("error", {}).get("message", "协议握手失败")
                error = error_msg
                return "offline", latency, 0, error, []

        except asyncio.TimeoutError:
            latency = int((time.time() - start_time) * 1000)
            error = "通信超时：服务器未响应initialize请求"
            return "offline", latency, 0, error, []

    except FileNotFoundError:
        latency = int((time.time() - start_time) * 1000)
        error = f"命令未找到: {command}。请确保后端容器已安装 Node.js，运行 docker compose build --no-cache backend && docker compose up -d 重建后端容器后重试"
        return "offline", latency, 0, error, []
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        error = str(e)
        return "offline", latency, 0, error, []
    finally:
        try:
            if process is not None and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
        except Exception:
            pass
