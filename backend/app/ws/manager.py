"""
WebSocket Manager
WebSocket连接管理器
"""

import json
from typing import Any
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """连接WebSocket"""
        await websocket.accept()
        self.active_connections[channel].append(websocket)

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """断开WebSocket连接"""
        if websocket in self.active_connections[channel]:
            self.active_connections[channel].remove(websocket)
        if not self.active_connections[channel]:
            del self.active_connections[channel]

    async def send_personal_message(
        self, message: dict[str, Any], websocket: WebSocket
    ) -> None:
        """发送个人消息"""
        await websocket.send_json(message)

    async def broadcast(
        self, channel: str, message: dict[str, Any]
    ) -> None:
        """广播消息到频道"""
        for connection in self.active_connections[channel]:
            await connection.send_json(message)

    async def broadcast_all(
        self, message: dict[str, Any]
    ) -> None:
        """广播消息到所有连接"""
        for channel in self.active_connections:
            await self.broadcast(channel, message)

    def get_connection_count(self, channel: str | None = None) -> int:
        """获取连接数量"""
        if channel:
            return len(self.active_connections.get(channel, []))
        return sum(len(conns) for conns in self.active_connections.values())


manager = ConnectionManager()


class WebSocketHandler:
    """WebSocket处理器"""

    def __init__(self, manager: ConnectionManager) -> None:
        self.manager = manager

    async def handle_admin_connection(self, websocket: WebSocket) -> None:
        """处理Admin WebSocket连接"""
        await self.manager.connect(websocket, "admin")

        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                await self._process_admin_message(message)

        except WebSocketDisconnect:
            self.manager.disconnect(websocket, "admin")

    async def handle_chat_connection(self, websocket: WebSocket, session_id: str) -> None:
        """处理Chat WebSocket连接"""
        channel = f"chat:{session_id}"
        await self.manager.connect(websocket, channel)

        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                await self._process_chat_message(session_id, message)

        except WebSocketDisconnect:
            self.manager.disconnect(websocket, channel)

    async def _process_admin_message(self, message: dict[str, Any]) -> None:
        """处理Admin消息"""
        msg_type = message.get("type")

        if msg_type == "ping":
            await self.manager.broadcast("admin", {"type": "pong"})

    async def _process_chat_message(self, session_id: str, message: dict[str, Any]) -> None:
        """处理Chat消息"""
        channel = f"chat:{session_id}"
        msg_type = message.get("type")

        if msg_type == "ping":
            await self.manager.broadcast(channel, {"type": "pong"})

        elif msg_type == "message":
            await self.manager.broadcast(channel, {
                "type": "message",
                "content": message.get("content"),
                "timestamp": message.get("timestamp"),
            })
