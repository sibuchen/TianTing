"""
Human Service Schemas
人工客服相关
"""

from pydantic import BaseModel, ConfigDict

from app.schemas.common import to_camel


class QueueItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    conversation_id: str
    user_id: str | None = None
    user_name: str | None = None
    user_avatar: str | None = None
    intent: str | None = None
    intent_icon: str | None = None
    channel: str = "web"
    waiting_duration: int = 0
    status: str
    last_message: dict | None = None


class QueueResponse(BaseModel):

    code: int = 0
    data: list[QueueItem] = []


class HumanSessionMessagesResponse(BaseModel):

    code: int = 0
    data: dict


class SendMessageRequest(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "content": "好的，我来帮您处理。"
    }}, alias_generator=to_camel, populate_by_name=True)

    content: str


class SendMessageResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    content: str
    timestamp: str | None = None


class QuickReplyItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    title: str
    content: str


class QuickReplyResponse(BaseModel):

    code: int = 0
    data: list[QuickReplyItem] = []
