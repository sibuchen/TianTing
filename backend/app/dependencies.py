"""
Dependencies
全局依赖注入
"""

from typing import AsyncGenerator

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_security_manager
from app.core.token_store import get_token_store
from app.models.user import User
from sqlalchemy import select, and_


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_session_id: str | None = Cookie(default=None, alias="session_id"),
) -> dict:
    """获取当前用户（支持 Bearer Token 和 Cookie 两种方式）"""
    token: str | None = None

    if auth_session_id:
        store = get_token_store()
        token = store.load_token(auth_session_id)
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
        )

    security_manager = get_security_manager()
    payload = security_manager.verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
        )

    return {
        "sub": payload.get("sub"),
        "username": payload.get("username"),
        "role": payload.get("role"),
    }


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)
    ),
    auth_session_id: str | None = Cookie(default=None, alias="session_id"),
) -> dict | None:
    """获取当前用户（可选）"""
    token: str | None = None

    if auth_session_id:
        store = get_token_store()
        token = store.load_token(auth_session_id)
    if not token and credentials:
        token = credentials.credentials

    if not token:
        return None

    try:
        security_manager = get_security_manager()
        payload = security_manager.verify_access_token(token)

        if payload:
            return {
                "sub": payload.get("sub"),
                "username": payload.get("username"),
                "role": payload.get("role"),
            }
    except Exception:
        pass

    return None


async def get_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """获取管理员用户"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限",
        )

    return current_user


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库Session"""
    async for session in get_db():
        yield session
