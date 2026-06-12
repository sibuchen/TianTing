"""
Tool Schemas
工具相关
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.schemas.common import to_camel


class BuiltinToolItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    name_en: str | None = None
    icon: str | None = None
    description: str | None = None
    category: str
    category_label: str | None = None
    category_icon: str | None = None
    is_enabled: bool


class BuiltinToolResponse(BaseModel):

    code: int = 0
    data: list[BuiltinToolItem] = []


class BuiltinToolToggleRequest(BaseModel):

    is_enabled: bool


class MCPServerCreate(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "ERP System",
        "transportType": "sse",
        "url": "https://erp.example.com/mcp"
    }}, alias_generator=to_camel, populate_by_name=True)

    name: str = Field(..., max_length=100)
    transport_type: Literal["sse", "stdio"] = "sse"
    url: HttpUrl | None = None
    command: str | None = Field(None, max_length=500)
    args: list[str] | None = None
    env: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_transport_fields(self):
        if self.transport_type == "sse" and not self.url:
            raise ValueError("SSE模式必须提供url")
        if self.transport_type == "stdio" and not self.command:
            raise ValueError("stdio模式必须提供command")
        return self


class MCPServerUpdate(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "ERP System V2",
        "url": "https://erp-v2.example.com/mcp"
    }}, alias_generator=to_camel, populate_by_name=True)

    name: str | None = Field(None, max_length=100)
    transport_type: Literal["sse", "stdio"] | None = None
    url: HttpUrl | None = None
    command: str | None = Field(None, max_length=500)
    args: list[str] | None = None
    env: dict[str, str] | None = None


class MCPServerToolItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    description: str | None = None


class MCPServerResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    transport_type: str = "sse"
    url: str | None = None
    command: str | None = None
    status: str
    tools_count: int = 0


class MCPServerDetail(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    transport_type: str = "sse"
    url: str | None = None
    command: str | None = None
    status: str
    tools_count: int = 0
    tools: list[MCPServerToolItem] = []
    created_at: str | None = None


class MCPServerTestResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    status: str
    latency: int
    tools_count: int
