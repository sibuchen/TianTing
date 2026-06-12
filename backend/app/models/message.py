"""
Message Model
消息表
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.conversation import Conversation


class Message(BaseModel):
    """消息表"""

    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tool_calls: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_system_message: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )
    agent: Mapped["Agent | None"] = relationship(
        "Agent",
        back_populates="messages",
    )

    __table_args__ = (
        {"comment": "消息表"},
    )

    def is_user_message(self) -> bool:
        """是否为用户消息"""
        return self.role == "user"

    def is_agent_message(self) -> bool:
        """是否为Agent消息"""
        return self.role == "agent"

    def is_human_agent_message(self) -> bool:
        """是否为人功客服消息"""
        return self.role == "human_agent"

    def is_system_message_type(self) -> bool:
        """是否为系统消息"""
        return self.role == "system" or self.is_system_message
