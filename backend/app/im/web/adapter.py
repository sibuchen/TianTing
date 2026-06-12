from typing import Any, AsyncGenerator

from app.im.base import IMAdapter


class WebAdapter(IMAdapter):
    @property
    def channel_name(self) -> str:
        return "web"

    async def send_message(self, recipient_id: str, content: str, **kwargs: Any) -> bool:
        return True

    async def send_streaming_message(self, recipient_id: str, stream: AsyncGenerator[str, None], **kwargs: Any) -> str:
        full_content = ""
        async for chunk in stream:
            full_content += chunk
        return full_content
