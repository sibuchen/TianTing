"""
Agent Schemas
Agent相关
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import to_camel


class SkillInfo(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    name_en: str | None = None
    icon: str | None = None


class MCPServerInfo(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    status: str


class ToolInfo(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    is_enabled: bool


class ModelInfo(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    provider: str | None = None


class AgentStats(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    total_conversations: int = 0
    resolution_rate: float = 0.0


class AgentListItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    type: str
    description: str | None = None
    icon: str | None = None
    icon_color: str | None = None
    is_enabled: bool
    model_name: str | None = None
    skills_count: int = 0
    tools_count: int = 0


class AgentBase(BaseModel):

    name: str = Field(..., max_length=50)
    type: Literal["orchestrator", "faq", "after-sale", "custom"]
    description: str | None = Field(None, max_length=200)


class AgentCreate(AgentBase):

    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "售后客服",
        "type": "after-sale",
        "description": "处理售后相关问题"
    }}, alias_generator=to_camel, populate_by_name=True)


class SubAgentInfo(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    type: str
    description: str | None = None
    is_enabled: bool = True


class KnowledgeDocInfo(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    file_name: str
    vector_status: str


class KnowledgeQAInfo(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    question: str


class AgentUpdate(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "主编排器 v2",
        "systemPrompt": "你是一个升级版的智能客服编排器...",
        "isEnabled": True
    }}, alias_generator=to_camel, populate_by_name=True)

    name: str | None = Field(None, max_length=50)
    type: Literal["orchestrator", "faq", "after-sale", "custom"] | None = None
    description: str | None = Field(None, max_length=200)
    system_prompt: str | None = Field(None, max_length=5000)
    is_enabled: bool | None = None
    model_config_id: str | None = None
    transfer_keywords: list[str] | None = None
    human_agent_id: str | None = None
    supported_channels: list[str] | None = None


class AgentDetail(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    type: str
    description: str | None = None
    system_prompt: str | None = None
    is_enabled: bool
    model_info: ModelInfo | None = None
    skills: list[SkillInfo] = []
    mcp_servers: list[MCPServerInfo] = []
    tools: list[ToolInfo] = []
    stats: AgentStats | None = None
    transfer_keywords: list[str] | None = None
    human_agent_id: str | None = None
    supported_channels: list[str] | None = None
    sub_agents: list[SubAgentInfo] | None = None
    knowledge_documents: list[KnowledgeDocInfo] | None = None
    knowledge_qa_list: list[KnowledgeQAInfo] | None = None


class AgentCreateResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    type: str
    description: str | None = None
    is_enabled: bool
    created_at: datetime


class SkillAssignRequest(BaseModel):

    pass


class MCPServerLinkRequest(BaseModel):

    mcp_server_id: str
    is_linked: bool


class ToolToggleRequest(BaseModel):

    is_enabled: bool
