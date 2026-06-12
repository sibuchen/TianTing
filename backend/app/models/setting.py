"""
Setting Model
系统设置表
"""

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Setting(BaseModel):
    """系统设置表"""

    __tablename__ = "settings"

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        {"comment": "系统设置表（KV结构）"},
    )
