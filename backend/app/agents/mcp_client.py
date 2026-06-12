"""
MCP Client
MCP客户端：连接/发现/调用，支持 SSE (HTTP) 和 stdio (子进程 JSON-RPC) 两种传输模式
"""

import asyncio
import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP客户端"""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        transport_type: str = "sse",
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.transport_type = transport_type
        self.base_url = base_url
        self.api_key = api_key
        self.command = command
        self.args = args or []
        self.mcp_env = env or {}
        self.tools: list[dict[str, Any]] = []
        self._process: asyncio.subprocess.Process | None = None
        self._request_id: int = 0
        self._stdio_lock = asyncio.Lock()

    async def connect(self) -> bool:
        """连接MCP Server"""
        if self.transport_type == "stdio":
            return await self._connect_stdio()
        return await self._connect_sse()

    async def _connect_sse(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/tools")
                if response.status_code == 200:
                    self.tools = response.json().get("tools", [])
                    return True
                return False
        except Exception:
            return False

    async def _connect_stdio(self) -> bool:
        if not self.command:
            logger.error("stdio mode requires a command")
            return False

        if self._process is not None and self._process.returncode is None:
            return True

        try:
            proc_env = {**os.environ, **self.mcp_env}
            self._process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=proc_env,
            )

            init_request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "tianting-test", "version": "1.0.0"},
                },
            }
            response = await self._send_stdio_request(init_request, timeout=15.0)
            if response is None:
                return False

            if "result" not in response:
                error_msg = response.get("error", {}).get("message", "协议握手失败")
                logger.error(f"MCP initialize failed: {error_msg}")
                return False

            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
            await self._send_stdio_notification(initialized_notification)

            logger.info(f"MCP stdio client connected: {self.command} {' '.join(self.args)}")
            return True
        except FileNotFoundError:
            logger.error(f"Command not found: {self.command}")
            return False
        except Exception as e:
            logger.error(f"stdio connect error: {e}")
            return False

    async def discover_tools(self) -> list[dict[str, Any]]:
        """发现可用工具"""
        if self.transport_type == "stdio":
            return await self._discover_tools_stdio()
        return self.tools

    async def _discover_tools_stdio(self) -> list[dict[str, Any]]:
        if not self._process or self._process.returncode is not None:
            connected = await self._connect_stdio()
            if not connected:
                return []

        try:
            tools_request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/list",
                "params": {},
            }
            response = await self._send_stdio_request(tools_request, timeout=10.0)
            if response is None:
                return []

            tools = response.get("result", {}).get("tools", [])
            self.tools = tools
            return tools
        except Exception as e:
            logger.error(f"stdio discover_tools error: {e}")
            return []

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """调用工具"""
        if self.transport_type == "stdio":
            return await self._call_tool_stdio(tool_name, arguments)
        return await self._call_tool_sse(tool_name, arguments)

    async def _call_tool_sse(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/tools/{tool_name}/call",
                    json=arguments,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                if response.status_code == 200:
                    return {"success": True, "result": response.json()}
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _call_tool_stdio(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._process or self._process.returncode is not None:
            connected = await self._connect_stdio()
            if not connected:
                return {"success": False, "error": "stdio进程未连接"}

        try:
            call_request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
            }
            response = await self._send_stdio_request(call_request, timeout=30.0)
            if response is None:
                return {"success": False, "error": "stdio工具调用超时"}

            if "error" in response:
                error_msg = response["error"].get("message", "未知错误")
                return {"success": False, "error": error_msg}

            result = response.get("result", {})
            content = result.get("content", [])
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            if text_parts:
                return {"success": True, "result": "\n".join(text_parts)}
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"stdio call_tool error: {e}")
            return {"success": False, "error": str(e)}

    async def test_connection(self) -> dict[str, Any]:
        """测试连接"""
        import time

        start_time = time.time()
        connected = await self.connect()
        latency = int((time.time() - start_time) * 1000)

        if connected and self.transport_type == "stdio":
            discovered = await self.discover_tools()
            return {
                "status": "online",
                "latency": max(latency, 1),
                "tools_count": len(discovered),
            }

        return {
            "status": "online" if connected else "offline",
            "latency": max(latency, 1),
            "tools_count": len(self.tools) if connected else 0,
        }

    async def close(self) -> None:
        """关闭连接，终止子进程"""
        if self._process is not None:
            try:
                if self._process.returncode is None:
                    self._process.terminate()
                    try:
                        await asyncio.wait_for(self._process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        self._process.kill()
                        await self._process.wait()
            except Exception:
                pass
            finally:
                self._process = None

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def _send_stdio_request(
        self, request: dict, timeout: float = 10.0
    ) -> dict | None:
        async with self._stdio_lock:
            if not self._process or self._process.stdin is None or self._process.stdout is None:
                return None

            message = json.dumps(request) + "\n"
            self._process.stdin.write(message.encode())
            await self._process.stdin.drain()

            try:
                response_line = await asyncio.wait_for(
                    self._process.stdout.readline(), timeout=timeout
                )
                return json.loads(response_line.decode().strip())
            except asyncio.TimeoutError:
                logger.error(f"stdio request timeout: {request.get('method', '')}")
                return None

    async def _send_stdio_notification(self, notification: dict) -> None:
        async with self._stdio_lock:
            if not self._process or self._process.stdin is None:
                return
            message = json.dumps(notification) + "\n"
            self._process.stdin.write(message.encode())
            await self._process.stdin.drain()

    def __del__(self) -> None:
        if self._process is not None and self._process.returncode is None:
            try:
                self._process.terminate()
            except Exception:
                pass


mcp_clients: dict[str, MCPClient] = {}


async def get_mcp_client(
    server_id: str,
    url: str | None = None,
    api_key: str | None = None,
    transport_type: str = "sse",
    command: str | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> MCPClient:
    """获取MCP客户端"""
    if server_id not in mcp_clients:
        mcp_clients[server_id] = MCPClient(
            base_url=url,
            api_key=api_key,
            transport_type=transport_type,
            command=command,
            args=args,
            env=env,
        )
        await mcp_clients[server_id].connect()

    return mcp_clients[server_id]