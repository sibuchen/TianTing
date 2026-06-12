"""
Auth API
认证模块
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.dependencies import get_current_user, get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    SendCodeRequest,
    ForgotPasswordRequest,
    UserInfo,
)
from app.schemas.common import BaseResponse
from app.services.auth_service import AuthService
from app.core.token_store import get_token_store
from app.core.captcha import generate_captcha, verify_captcha
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    req: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """用户登录"""
    service = AuthService(db)
    login_result = await service.login(
        username=data.username,
        password=data.password,
        remember=data.remember,
    )

    store = get_token_store()
    session_id = store.save_token(login_result.token)

    cookie_max_age = None
    if data.remember:
        cookie_max_age = 30 * 24 * 3600

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=req.url.scheme == "https",
        samesite="lax",
        max_age=cookie_max_age,
        path="/",
    )

    return login_result


@router.get("/captcha")
async def get_captcha():
    """获取图片验证码"""
    captcha_id, _answer, captcha_image = await generate_captcha()
    return BaseResponse(
        data={
            "captchaId": captcha_id,
            "captchaImage": captcha_image,
        }
    )


@router.post("/register", response_model=LoginResponse)
async def register(
    request: RegisterRequest,
    req: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """用户注册"""
    if not await verify_captcha(request.captchaId, request.captchaCode):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    service = AuthService(db)
    login_result = await service.register(
        username=request.username,
        email=request.email,
        password=request.password,
        phone=request.phone,
    )

    store = get_token_store()
    session_id = store.save_token(login_result.token)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=req.url.scheme == "https",
        samesite="lax",
        path="/",
    )

    return login_result


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenResponse:
    """刷新Token"""
    service = AuthService(db)
    return await service.refresh_token(refresh_token=request.refreshToken)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LogoutResponse:
    """用户登出"""
    service = AuthService(db)
    await service.logout(current_user["sub"])

    response.delete_cookie(key="session_id", path="/")

    return LogoutResponse()


@router.get("/me", response_model=BaseResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取当前用户信息"""
    service = AuthService(db)
    user = await service.get_user_by_id(current_user["sub"])
    if not user:
        from app.core.exceptions import InvalidCredentialsError
        raise InvalidCredentialsError()
    return BaseResponse(
        data=UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            avatar=user.avatar,
        )
    )


@router.post("/send-code", response_model=BaseResponse)
async def send_code(
    request: SendCodeRequest,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """发送邮箱验证码"""
    service = AuthService(db)
    await service.send_code(email=request.email)
    return BaseResponse(message="验证码已发送")


@router.post("/forgot-password", response_model=BaseResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """忘记密码"""
    service = AuthService(db)
    await service.forgot_password(email=request.email)
    return BaseResponse(message="密码重置链接已发送到邮箱")
