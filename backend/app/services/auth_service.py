"""
Auth Service
认证服务：注册/登录/JWT/密码
"""

from datetime import datetime, timezone

from sqlalchemy import select, update, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import security_manager, get_security_manager
from app.core.exceptions import (
    InvalidCredentialsError,
    UserExistsError,
    PasswordTooShortError,
    InvalidRefreshTokenError,
    PasswordMismatchError,
)
from app.models.user import User, RefreshToken
from app.schemas.auth import LoginResponse, RefreshTokenResponse, UserInfo


class AuthService:
    """认证服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.security = get_security_manager()

    async def login(
        self, username: str, password: str, remember: bool = False
    ) -> LoginResponse:
        """用户登录"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user or not self.security.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        if user.status != "active":
            raise InvalidCredentialsError()

        token, expires_in = self.security.create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            remember=remember,
        )

        refresh_token, expires_at = self.security.create_refresh_token(
            user_id=user.id,
            remember=remember,
        )

        token_hash = self.security.hash_token(refresh_token)
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(refresh_token_record)

        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login_at=datetime.now(timezone.utc))
        )

        await self.db.commit()

        return LoginResponse(
            token=token,
            expires_in=expires_in,
            user=UserInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                avatar=user.avatar,
            ),
        )

    async def register(
        self, username: str, email: str, password: str, phone: str
    ) -> LoginResponse:
        """用户注册"""
        if not self.security.validate_password_strength(password):
            raise PasswordTooShortError()

        result = await self.db.execute(
            select(User).where(
                (User.username == username) | (User.email == email) | (User.phone == phone)
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == username:
                raise UserExistsError("用户名")
            if existing_user.email == email:
                raise UserExistsError("邮箱")
            raise UserExistsError("手机号")

        password_hash = self.security.hash_password(password)

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            phone=phone,
            role="operator",
            status="active",
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        token, expires_in = self.security.create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
        )

        refresh_token, expires_at = self.security.create_refresh_token(user_id=user.id)

        token_hash = self.security.hash_token(refresh_token)
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(refresh_token_record)

        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login_at=datetime.now(timezone.utc))
        )

        await self.db.commit()

        return LoginResponse(
            token=token,
            expires_in=expires_in,
            user=UserInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                avatar=user.avatar,
            ),
        )

    async def refresh_token(self, refresh_token: str) -> RefreshTokenResponse:
        """刷新Token"""
        payload = self.security.verify_refresh_token(refresh_token)
        if not payload:
            raise InvalidRefreshTokenError()

        token_hash = self.security.hash_token(refresh_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        stored_token = result.scalar_one_or_none()

        if not stored_token:
            raise InvalidRefreshTokenError()

        await self.db.execute(
            delete(RefreshToken).where(RefreshToken.id == stored_token.id)
        )

        user_result = await self.db.execute(
            select(User).where(User.id == stored_token.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise InvalidRefreshTokenError()

        new_token, expires_in = self.security.create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
        )

        new_refresh_token, new_expires_at = self.security.create_refresh_token(
            user_id=user.id
        )
        new_token_hash = self.security.hash_token(new_refresh_token)
        new_refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
        )
        self.db.add(new_refresh_token_record)

        await self.db.commit()

        return RefreshTokenResponse(token=new_token, expires_in=expires_in)

    async def logout(self, user_id: str) -> None:
        """用户登出"""
        await self.db.execute(
            delete(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        await self.db.commit()

    async def send_code(self, email: str) -> None:
        """发送邮箱验证码（MVP桩接口）"""
        pass

    async def forgot_password(self, email: str) -> None:
        """忘记密码（MVP桩接口）"""
        pass

    async def get_user_by_id(self, user_id: str) -> User | None:
        """根据ID获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> None:
        """修改密码"""
        if new_password != confirm_password:
            raise PasswordMismatchError()

        if not self.security.validate_password_strength(new_password):
            raise PasswordTooShortError()

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise InvalidCredentialsError()

        if not self.security.verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError()

        password_hash = self.security.hash_password(new_password)
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password_hash)
        )
        await self.db.commit()
