"""
Dashboard Schemas
仪表盘相关
"""

from pydantic import BaseModel, ConfigDict

from app.schemas.common import to_camel


class MetricsResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    data: dict


class RealtimeStatusResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    data: dict


class IntentDistributionItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    intent: str
    count: int
    percentage: float


class IntentDistributionResponse(BaseModel):

    code: int = 0
    data: list[IntentDistributionItem] = []


class ChannelDistributionItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    channel: str
    count: int
    percentage: float


class ChannelDistributionResponse(BaseModel):

    code: int = 0
    data: list[ChannelDistributionItem] = []


class RecentConversationItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    user_name: str | None = None
    user_avatar: str | None = None
    intent: str | None = None
    time: str | None = None
    status: str


class RecentConversationsResponse(BaseModel):

    code: int = 0
    data: list[RecentConversationItem] = []
