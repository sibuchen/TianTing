"""
Skill Schemas
技能相关
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import to_camel


class SkillCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {
            "name": "sales-skill",
            "displayName": "推销skill",
            "icon": "campaign",
            "iconColor": "#1890ff",
            "category": "sales",
            "description": "引导客户了解产品优势并促进购买决策",
            "tags": ["sales", "recommendation"],
            "skillBody": "...",
            "version": "1.0.0",
            "author": "admin",
            "prompts": "你是一个专业的销售助手，请根据客户需求推荐合适的产品。"
        }},
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(..., max_length=64, pattern=r"^[a-z0-9-]+$")
    display_name: str | None = Field(None, max_length=200)
    icon: str | None = Field(None, max_length=50)
    icon_color: str | None = Field(None, max_length=10)
    category: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=1024)
    tags: list[str] | None = None
    skill_body: str | None = None
    version: str | None = Field(None, max_length=20)
    author: str | None = Field(None, max_length=100)
    prompts: str | None = None


class SkillUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {
            "name": "advanced-sales-skill",
            "displayName": "高级推销skill",
            "description": "引导客户了解产品优势并促进购买决策（升级版）"
        }},
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str | None = Field(None, max_length=64, pattern=r"^[a-z0-9-]+$")
    display_name: str | None = Field(None, max_length=200)
    icon: str | None = Field(None, max_length=50)
    icon_color: str | None = Field(None, max_length=10)
    category: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=1024)
    status: str | None = Field(None, pattern=r"^(active|inactive)$")
    tags: list[str] | None = None
    skill_body: str | None = None
    version: str | None = Field(None, max_length=20)
    author: str | None = Field(None, max_length=100)
    prompts: str | None = None


class SkillResourceResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    skill_id: str
    file_name: str
    file_path: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    created_at: datetime


class SkillResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    name: str
    display_name: str | None = None
    icon: str | None = None
    icon_color: str | None = None
    category: str
    description: str | None = None
    status: str
    skill_body: str | None = None
    tags: list[str] | None = None
    version: str | None = None
    author: str | None = None
    prompts: str | None = None
    is_builtin: bool = True
    resources: list[SkillResourceResponse] | None = None