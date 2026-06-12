"""
User Models
用户表 + 刷新令牌表
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.human_session import HumanSession


class User(BaseModel):
    """管理后台用户表"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="operator")
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    human_sessions: Mapped[list["HumanSession"]] = relationship(
        "HumanSession",
        back_populates="operator",
        foreign_keys="HumanSession.operator_id",
    )

    __table_args__ = (
        {"comment": "管理后台用户表"},
    )

    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == "admin"

    def is_active(self) -> bool:
        """是否启用"""
        return self.status == "active"


class RefreshToken(BaseModel):
    """刷新令牌表"""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        {"comment": "JWT刷新令牌表"},
    )

    def is_expired(self) -> bool:
        """是否过期"""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at
