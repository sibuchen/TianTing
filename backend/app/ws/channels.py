"""
Channels
频道管理
"""

from typing import Any

from app.ws.manager import manager


class ChannelManager:
    """频道管理器"""

    @staticmethod
    async def subscribe(channel: str, websocket) -> None:
        """订阅频道"""
        await manager.connect(websocket, channel)

    @staticmethod
    async def unsubscribe(channel: str, websocket) -> None:
        """取消订阅"""
        manager.disconnect(websocket, channel)

    @staticmethod
    async def publish(channel: str, message: dict[str, Any]) -> None:
        """发布消息"""
        await manager.broadcast(channel, message)

    @staticmethod
    async def publish_realtime_status(status: dict[str, Any]) -> None:
        """发布实时状态"""
        await manager.broadcast("admin", {
            "type": "realtime_status",
            "data": status,
        })

    @staticmethod
    async def publish_new_conversation(conversation: dict[str, Any]) -> None:
        """发布新对话"""
        await manager.broadcast("admin", {
            "type": "new_conversation",
            "data": conversation,
        })

    @staticmethod
    async def publish_conversation_update(conversation_id: str, update: dict[str, Any]) -> None:
        """发布对话更新"""
        await manager.broadcast("admin", {
            "type": "conversation_update",
            "conversationId": conversation_id,
            "data": update,
        })

    @staticmethod
    async def publish_message(session_id: str, message: dict[str, Any]) -> None:
        """发布消息到聊天会话"""
        channel = f"chat:{session_id}"
        await manager.broadcast(channel, {
            "type": "message",
            "data": message,
        })


channels = ChannelManager()
