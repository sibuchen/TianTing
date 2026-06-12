"""
Conversation Model
对话会话表
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.human_session import HumanSession
    from app.models.message import Message


class Conversation(BaseModel):
    """对话会话表"""

    __tablename__ = "conversations"

    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    handled_by: Mapped[str] = mapped_column(String(20), nullable=False, default="agent")
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="web", index=True)
    feishu_open_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    feishu_chat_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    human_session: Mapped["HumanSession | None"] = relationship(
        "HumanSession",
        back_populates="conversation",
        uselist=False,
    )

    __table_args__ = (
        {"comment": "对话会话表"},
    )

    def is_active(self) -> bool:
        """是否进行中"""
        return self.status == "active"

    def is_resolved(self) -> bool:
        """是否已解决"""
        return self.status == "resolved"

    def is_transferred(self) -> bool:
        """是否已转人工"""
        return self.status == "transferred"

    def is_pending(self) -> bool:
        """是否待处理"""
        return self.status == "pending"

    def is_handled_by_agent(self) -> bool:
        """是否由Agent处理"""
        return self.handled_by == "agent"

    def is_handled_by_human(self) -> bool:
        """是否由人工处理"""
        return self.handled_by == "human"
