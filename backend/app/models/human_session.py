"""
Human Session Model
人工客服会话表
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.conversation import Conversation
    from app.models.user import User


class HumanSession(BaseModel):
    """人工客服会话表"""

    __tablename__ = "human_sessions"

    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conversations.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    agent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="waiting", index=True)
    operator_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="human_session",
    )
    agent: Mapped["Agent | None"] = relationship(
        "Agent",
        back_populates="human_sessions",
    )
    operator: Mapped["User | None"] = relationship(
        "User",
        back_populates="human_sessions",
        foreign_keys=[operator_id],
    )

    __table_args__ = (
        {"comment": "人工客服会话表"},
    )

    def is_waiting(self) -> bool:
        """是否等待中"""
        return self.status == "waiting"

    def is_active(self) -> bool:
        """是否进行中"""
        return self.status == "active"

    def is_ended(self) -> bool:
        """是否已结束"""
        return self.status == "ended"
