from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.im.base import IMAdapter, IncomingMessage


@dataclass
class IMMessage:
    platform: str
    user_id: str
    chat_id: str
    content: str
    message_id: str | None = None
    raw_event: dict[str, Any] = field(default_factory=dict)


class IMClient(ABC):

    @abstractmethod
    async def send_message(self, user_id: str, text: str) -> bool:
        ...

    @abstractmethod
    async def reply_message(self, message_id: str, text: str) -> bool:
        ...

    @abstractmethod
    async def get_user_name(self, user_id: str) -> str | None:
        ...


__all__ = ["IMMessage", "IMClient", "IMAdapter", "IncomingMessage"]
