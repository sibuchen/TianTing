"""
Agent Models
Agent表 + Agent-Skill关联表 + Agent-MCP Server关联表 + Agent-Tool关联表
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.conversation import Conversation
    from app.models.human_session import HumanSession
    from app.models.knowledge import KnowledgeDocument, KnowledgeQA
    from app.models.message import Message
    from app.models.mcp_server import MCPServer
    from app.models.model_config import ModelConfig
    from app.models.skill import Skill
    from app.models.tool import ToolConfig


class Agent(BaseModel):
    """Agent配置表"""

    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    icon_color: Mapped[str | None] = mapped_column(String(10), nullable=True)
    model_config_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("model_configs.id", ondelete="SET NULL"),
        nullable=True,
    )
    transfer_keywords: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    human_agent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    supported_channels: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    model_config: Mapped["ModelConfig | None"] = relationship(
        "ModelConfig",
        back_populates="agents",
    )
    skills: Mapped[list["AgentSkill"]] = relationship(
        "AgentSkill",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    mcp_servers: Mapped[list["AgentMCPServer"]] = relationship(
        "AgentMCPServer",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    tools: Mapped[list["AgentTool"]] = relationship(
        "AgentTool",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="agent",
    )
    human_sessions: Mapped[list["HumanSession"]] = relationship(
        "HumanSession",
        back_populates="agent",
    )
    sub_agents: Mapped[list["AgentSubAgent"]] = relationship(
        "AgentSubAgent",
        foreign_keys="AgentSubAgent.parent_agent_id",
        back_populates="parent_agent",
        cascade="all, delete-orphan",
    )
    parent_agents: Mapped[list["AgentSubAgent"]] = relationship(
        "AgentSubAgent",
        foreign_keys="AgentSubAgent.sub_agent_id",
        back_populates="sub_agent",
        cascade="all, delete-orphan",
    )
    knowledge_documents: Mapped[list["AgentKnowledgeDocument"]] = relationship(
        "AgentKnowledgeDocument",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    knowledge_qa_list: Mapped[list["AgentKnowledgeQA"]] = relationship(
        "AgentKnowledgeQA",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        {"comment": "Agent配置表"},
    )

    def is_orchestrator(self) -> bool:
        """是否为编排Agent"""
        return self.type == "orchestrator"


class AgentSkill(Base):
    """Agent-Skill关联表"""

    __tablename__ = "agent_skills"
    __table_args__ = (
        {"comment": "Agent-Skill多对多关联表"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="agent_skills")


class AgentMCPServer(Base):
    """Agent-MCP Server关联表"""

    __tablename__ = "agent_mcp_servers"
    __table_args__ = (
        {"comment": "Agent-MCP Server多对多关联表"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    mcp_server_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("mcp_servers.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_linked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="mcp_servers")
    mcp_server: Mapped["MCPServer"] = relationship(
        "MCPServer",
        back_populates="agent_mcp_servers",
    )


class AgentTool(Base):
    """Agent-Tool关联表"""

    __tablename__ = "agent_tools"
    __table_args__ = (
        {"comment": "Agent-Tool多对多关联表"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_config_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tool_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="tools")
    tool_config: Mapped["ToolConfig"] = relationship(
        "ToolConfig",
        back_populates="agent_tools",
    )


class AgentSubAgent(Base):
    __tablename__ = "agent_sub_agents"
    __table_args__ = (
        {"comment": "主智能体-SubAgent关联表"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    parent_agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    sub_agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    parent_agent: Mapped["Agent"] = relationship(
        "Agent", foreign_keys=[parent_agent_id], back_populates="sub_agents"
    )
    sub_agent: Mapped["Agent"] = relationship(
        "Agent", foreign_keys=[sub_agent_id], back_populates="parent_agents"
    )


class AgentKnowledgeDocument(Base):
    __tablename__ = "agent_knowledge_documents"
    __table_args__ = (
        {"comment": "Agent-知识库文档关联表"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="knowledge_documents")
    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument", back_populates="agent_links"
    )


class AgentKnowledgeQA(Base):
    __tablename__ = "agent_knowledge_qa"
    __table_args__ = (
        {"comment": "Agent-QA关联表"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    qa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("knowledge_qa.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="knowledge_qa_list")
    qa: Mapped["KnowledgeQA"] = relationship(
        "KnowledgeQA", back_populates="agent_links"
    )
