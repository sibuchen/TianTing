"""
Auth Schemas
认证相关
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import to_camel


class LoginRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "username": "admin",
        "password": "Admin@123456",
        "remember": False
    }})

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    remember: bool = False


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    username: str
    email: str
    role: str
    avatar: str | None = None


class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    token: str
    expires_in: int
    user: UserInfo


class RegisterRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "username": "new_user",
        "email": "newuser@example.com",
        "password": "NewUser@123",
        "phone": "13800138000",
        "captchaId": "captcha_abc123",
        "captchaCode": "123456"
    }})

    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str = Field(..., min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$")
    captchaId: str
    captchaCode: str


class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }})

    refreshToken: str = Field(..., min_length=1)


class RefreshTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    token: str
    expires_in: int


class SendCodeRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "email": "user@example.com"
    }})

    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "email": "user@example.com"
    }})

    email: EmailStr


class LogoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    message: str = "登出成功"


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {
            "username": "new_user",
            "email": "newuser@example.com",
            "password": "NewUser@123",
            "role": "operator"
        }},
        alias_generator=to_camel,
        populate_by_name=True,
    )

    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field("operator", pattern=r"^(admin|operator)$")


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {
            "email": "updated@example.com",
            "role": "admin"
        }},
        alias_generator=to_camel,
        populate_by_name=True,
    )

    username: str | None = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr | None = None
    role: str | None = Field(None, pattern=r"^(admin|operator)$")
    password: str | None = Field(None, min_length=8)
