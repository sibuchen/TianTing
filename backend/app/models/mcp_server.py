"""
MCP Server Model
MCP Server配置表
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.agent import AgentMCPServer
    from app.models.tool import ToolConfig


class MCPServer(BaseModel):
    """MCP Server配置表"""

    __tablename__ = "mcp_servers"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    transport_type: Mapped[str] = mapped_column(String(20), nullable=False, default="sse")
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    command: Mapped[str | None] = mapped_column(String(500), nullable=True)
    args: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    env: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="offline", index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tools: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    agent_mcp_servers: Mapped[list["AgentMCPServer"]] = relationship(
        "AgentMCPServer",
        back_populates="mcp_server",
        cascade="all, delete-orphan",
    )
    tool_configs: Mapped[list["ToolConfig"]] = relationship(
        "ToolConfig",
        back_populates="mcp_server",
    )

    __table_args__ = (
        {"comment": "MCP Server配置表"},
    )

    def is_online(self) -> bool:
        """是否在线"""
        return self.status == "online"

    def is_sse(self) -> bool:
        """是否为SSE模式"""
        return self.transport_type == "sse"

    def is_stdio(self) -> bool:
        """是否为stdio模式"""
        return self.transport_type == "stdio"
