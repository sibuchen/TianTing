"""
MCP Service
MCP Server管理服务：stdio进程管理 + 工具发现
"""

import asyncio
import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_server import MCPServer

logger = logging.getLogger(__name__)

_process_registry: dict[str, asyncio.subprocess.Process] = {}


class MCPService:
    """MCP Server管理服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def start_stdio_server(self, server_id: str) -> dict:
        """启动stdio模式的MCP Server子进程"""
        from sqlalchemy import select, update

        result = await self.db.execute(
            select(MCPServer).where(MCPServer.id == server_id)
        )
        server = result.scalar_one_or_none()

        if not server:
            return {"success": False, "message": "MCP Server不存在"}

        if not server.is_stdio():
            return {"success": False, "message": "仅stdio模式支持启动"}

        if server_id in _process_registry and _process_registry[server_id].returncode is None:
            return {"success": False, "message": "进程已在运行中"}

        try:
            cmd = server.command
            args = server.args or []
            env_vars = server.env or {}

            import os
            proc_env = {**os.environ, **env_vars}

            process = await asyncio.create_subprocess_exec(
                cmd,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=proc_env,
            )

            _process_registry[server_id] = process

            await self.db.execute(
                update(MCPServer)
                .where(MCPServer.id == server_id)
                .values(status="online")
            )
            await self.db.commit()

            logger.info(f"Started stdio MCP Server: {server.name} (PID: {process.pid})")

            return {
                "success": True,
                "message": f"进程已启动 (PID: {process.pid})",
                "pid": process.pid,
            }
        except Exception as e:
            logger.error(f"Failed to start stdio MCP Server {server.name}: {e}")
            return {"success": False, "message": f"启动失败: {str(e)}"}

    async def stop_stdio_server(self, server_id: str) -> dict:
        """停止stdio模式的MCP Server子进程"""
        from sqlalchemy import update

        if server_id not in _process_registry:
            return {"success": False, "message": "进程未在运行"}

        process = _process_registry[server_id]

        if process.returncode is not None:
            del _process_registry[server_id]
            return {"success": False, "message": "进程已退出"}

        try:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

            del _process_registry[server_id]

            await self.db.execute(
                update(MCPServer)
                .where(MCPServer.id == server_id)
                .values(status="offline")
            )
            await self.db.commit()

            return {"success": True, "message": "进程已停止"}
        except Exception as e:
            return {"success": False, "message": f"停止失败: {str(e)}"}

    async def check_stdio_health(self, server_id: str) -> dict:
        """检查stdio进程健康状态"""
        if server_id not in _process_registry:
            return {"alive": False, "message": "进程未启动"}

        process = _process_registry[server_id]
        is_alive = process.returncode is None

        if not is_alive:
            from sqlalchemy import update
            await self.db.execute(
                update(MCPServer)
                .where(MCPServer.id == server_id)
                .values(status="offline")
            )
            await self.db.commit()
            del _process_registry[server_id]

        return {
            "alive": is_alive,
            "pid": process.pid if is_alive else None,
            "returncode": process.returncode,
        }

    async def discover_stdio_tools(self, server_id: str) -> dict:
        """通过stdio通信发现MCP Server提供的工具列表"""
        if server_id not in _process_registry:
            return {"success": False, "message": "进程未启动", "tools": []}

        process = _process_registry[server_id]
        if process.returncode is not None:
            return {"success": False, "message": "进程已退出", "tools": []}

        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            }
            message = json.dumps(request) + "\n"

            process.stdin.write(message.encode())
            await process.stdin.drain()

            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=10.0
            )
            response = json.loads(response_line.decode().strip())

            tools = response.get("result", {}).get("tools", [])

            from sqlalchemy import update
            await self.db.execute(
                update(MCPServer)
                .where(MCPServer.id == server_id)
                .values(tools=tools)
            )
            await self.db.commit()

            return {"success": True, "tools": tools}
        except asyncio.TimeoutError:
            return {"success": False, "message": "通信超时", "tools": []}
        except Exception as e:
            return {"success": False, "message": str(e), "tools": []}
