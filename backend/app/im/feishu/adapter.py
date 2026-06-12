from typing import Any, AsyncGenerator

from app.im.base import IMAdapter, IncomingMessage
from app.im.feishu.client import get_feishu_client


class FeishuAdapter(IMAdapter):
    @property
    def channel_name(self) -> str:
        return "feishu"

    async def send_message(self, recipient_id: str, content: str, **kwargs: Any) -> bool:
        feishu_client = get_feishu_client()
        return await feishu_client.send_message(recipient_id, content)

    async def send_streaming_message(self, recipient_id: str, stream: AsyncGenerator[str, None], **kwargs: Any) -> str:
        full_content = ""
        async for chunk in stream:
            full_content += chunk
        feishu_client = get_feishu_client()
        await feishu_client.send_message(recipient_id, full_content)
        return full_content
