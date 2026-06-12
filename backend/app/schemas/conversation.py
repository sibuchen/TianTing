"""
Conversation Schemas
会话相关
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import to_camel


class ToolCallItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str
    arguments: str | None = None
    result: str | None = None


class MessageItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    role: str
    content: str
    timestamp: str | None = None
    type: str = "text"
    agent_name: str | None = None
    tool_calls: list[ToolCallItem] | None = None
    is_system_message: bool = False


class SessionCreateRequest(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "user_id": "user_001",
        "user_name": "张三",
        "user_avatar": "https://example.com/avatar.png"
    }}, alias_generator=to_camel, populate_by_name=True)

    user_id: str | None = None
    user_name: str | None = None
    user_avatar: str | None = None


class SessionCreateResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    session_id: str
    conversation_id: str
    status: str
    channel: str = "web"
    welcome_message: str | None = None


class SessionInfoResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    session_id: str
    conversation_id: str
    status: str
    channel: str = "web"
    handled_by: str | None = None
    message_count: int = 0
    created_at: str | None = None


class MessageListData(BaseModel):

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    messages: list[MessageItem]
    has_more: bool


class MessageListResponse(BaseModel):

    code: int = 0
    data: MessageListData


class ChatMessageRequest(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "content": "我要退款",
        "message_type": "text"
    }}, alias_generator=to_camel, populate_by_name=True)

    content: str
    message_type: str = "text"


class ChatStatusResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    status: str
    handled_by: str | None = None
    agent_name: str | None = None


class FeedbackRequest(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "message_id": "msg_001",
        "feedback_type": "up",
        "comment": "回答很准确"
    }}, alias_generator=to_camel, populate_by_name=True)

    message_id: str
    feedback_type: str = Field(..., pattern="^(up|down)$")
    comment: str | None = None


class HistoryListItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    user_name: str | None = None
    user_id: str | None = None
    user_avatar: str | None = None
    intent: str | None = None
    intent_icon: str | None = None
    status: str
    started_at: str | None = None
    ended_at: str | None = None
    duration: int = 0
    message_count: int = 0
    handled_by: str | None = None
    channel: str = "web"
    preview: str | None = None


class HistoryListData(BaseModel):

    items: list[HistoryListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class HistoryListResponse(BaseModel):

    code: int = 0
    data: HistoryListData


class HistoryDetailData(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    user_name: str | None = None
    user_id: str | None = None
    user_avatar: str | None = None
    intent: str | None = None
    status: str
    channel: str = "web"
    started_at: str | None = None
    ended_at: str | None = None
    messages: list[MessageItem] = []


class HistoryDetailResponse(BaseModel):

    code: int = 0
    data: HistoryDetailData
