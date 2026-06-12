"""
Model Config Model
模型API配置表
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agent import Agent


class ModelConfig(BaseModel):
    """模型API配置表"""

    __tablename__ = "model_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key_enc: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_iv: Mapped[str] = mapped_column(String(32), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    capabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    context_window: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal", index=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        back_populates="model_config",
    )

    __table_args__ = (
        {"comment": "模型API配置表"},
    )

    def is_normal(self) -> bool:
        """是否正常"""
        return self.status == "normal"
