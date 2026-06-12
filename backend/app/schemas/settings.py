"""
Settings Schemas
设置相关
"""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import to_camel


class UserSettings(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    username: str
    email: str
    role: str
    avatar: str | None = None


class AppearanceSettings(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    theme: str = "light"
    language: str = "zh-CN"
    sidebar_collapsed: bool = False


class NotificationSettings(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    email_enabled: bool = True
    sound_enabled: bool = True
    desktop_notifications: bool = True


class ChatWidgetSettings(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    primary_color: str = "#6366F1"
    position: str = "right"
    welcome_message: str = "您好，有什么可以帮您？"


class AboutSettings(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    version: str
    build_date: str | None = None


class SettingsResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    data: dict


class AppearanceUpdate(BaseModel):

    theme: str | None = None
    language: str | None = None
    sidebar_collapsed: bool | None = None


class NotificationUpdate(BaseModel):

    email_enabled: bool | None = None
    sound_enabled: bool | None = None
    desktop_notifications: bool | None = None


class ChatWidgetUpdate(BaseModel):

    primary_color: str | None = None
    position: str | None = None
    welcome_message: str | None = None


class SettingsUpdateRequest(BaseModel):

    appearance: AppearanceUpdate | None = None
    notifications: NotificationUpdate | None = None
    chat_widget: ChatWidgetUpdate | None = None


class AvatarUploadResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    data: dict


class PasswordChangeRequest(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "currentPassword": "OldPassword@123",
        "newPassword": "NewPassword@123",
        "confirmPassword": "NewPassword@123"
    }}, alias_generator=to_camel, populate_by_name=True)

    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class UpdateCheckResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    data: dict
