"""
Tool Config Model
工具配置表
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agent import AgentTool
    from app.models.mcp_server import MCPServer


class ToolConfig(BaseModel):
    """工具配置表"""

    __tablename__ = "tool_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(100), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category_icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tool_type: Mapped[str] = mapped_column(String(20), nullable=False, default="builtin", index=True)
    endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mcp_server_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("mcp_servers.id", ondelete="SET NULL"),
        nullable=True,
    )

    mcp_server: Mapped["MCPServer | None"] = relationship(
        "MCPServer",
        back_populates="tool_configs",
    )
    agent_tools: Mapped[list["AgentTool"]] = relationship(
        "AgentTool",
        back_populates="tool_config",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        {"comment": "工具配置表（统一管理内置工具和MCP工具）"},
    )
