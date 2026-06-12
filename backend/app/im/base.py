from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator


@dataclass
class IncomingMessage:
    channel: str
    content: str
    user_id: str | None = None
    user_name: str | None = None
    conversation_id: str | None = None
    session_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class IMAdapter(ABC):
    @abstractmethod
    async def send_message(self, recipient_id: str, content: str, **kwargs: Any) -> bool:
        ...

    @abstractmethod
    async def send_streaming_message(self, recipient_id: str, stream: AsyncGenerator[str, None], **kwargs: Any) -> str:
        ...

    @property
    @abstractmethod
    def channel_name(self) -> str:
        ...
