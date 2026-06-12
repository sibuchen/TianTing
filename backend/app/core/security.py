"""
Security Utilities
安全工具：JWT/AES/bcrypt
"""

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


class SecurityManager:
    """安全管理器"""

    def __init__(self) -> None:
        self._aesgcm: AESGCM | None = None

    def init(self) -> None:
        """初始化加密器"""
        key = settings.encryption_key.encode("utf-8")
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        self._aesgcm = AESGCM(key)

    @property
    def aesgcm(self) -> AESGCM:
        """获取AES-GCM加密器"""
        if self._aesgcm is None:
            raise RuntimeError("SecurityManager not initialized")
        return self._aesgcm

    def hash_password(self, password: str) -> str:
        """哈希密码"""
        salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    def create_access_token(
        self,
        user_id: str,
        username: str,
        role: str,
        remember: bool = False,
        additional_claims: dict[str, Any] | None = None,
    ) -> tuple[str, int]:
        """
        创建访问令牌
        返回: (token, expires_in_seconds)
        """
        if remember:
            expires_delta = timedelta(days=settings.jwt_access_token_expire_days_remember)
        else:
            expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

        expire = datetime.now(timezone.utc) + expires_delta
        expires_in = int(expires_delta.total_seconds())

        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        return token, expires_in

    def create_refresh_token(self, user_id: str, remember: bool = False) -> tuple[str, datetime]:
        """
        创建刷新令牌
        返回: (token, expires_at)
        """
        if remember:
            expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days_remember)
        else:
            expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)

        expires_at = datetime.now(timezone.utc) + expires_delta

        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expires_at,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16),
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        return token, expires_at

    def decode_token(self, token: str) -> dict[str, Any] | None:
        """解码令牌"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def verify_access_token(self, token: str) -> dict[str, Any] | None:
        """验证访问令牌"""
        payload = self.decode_token(token)
        if payload and payload.get("type") == "access":
            return payload
        return None

    def verify_refresh_token(self, token: str) -> dict[str, Any] | None:
        """验证刷新令牌"""
        payload = self.decode_token(token)
        if payload and payload.get("type") == "refresh":
            return payload
        return None

    def hash_token(self, token: str) -> str:
        """哈希令牌（用于存储）"""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def encrypt_api_key(self, api_key: str) -> tuple[str, str]:
        """
        加密API Key
        返回: (encrypted_key, iv_base64)
        """
        iv = secrets.token_bytes(12)
        encrypted = self.aesgcm.encrypt(iv, api_key.encode("utf-8"), None)
        return base64.b64encode(encrypted).decode("utf-8"), base64.b64encode(iv).decode("utf-8")

    def decrypt_api_key(self, encrypted_key: str, iv_base64: str) -> str:
        """解密API Key"""
        encrypted = base64.b64decode(encrypted_key.encode("utf-8"))
        iv = base64.b64decode(iv_base64.encode("utf-8"))
        decrypted = self.aesgcm.decrypt(iv, encrypted, None)
        return decrypted.decode("utf-8")

    def mask_api_key(self, api_key: str) -> str:
        """掩码API Key"""
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return f"{api_key[:4]}****{api_key[-4:]}"

    def generate_uuid(self) -> str:
        """生成UUID"""
        return secrets.token_uuid()

    def validate_password_strength(self, password: str) -> bool:
        """验证密码强度"""
        if len(password) < settings.password_min_length:
            return False
        return True


security_manager = SecurityManager()


def get_security_manager() -> SecurityManager:
    """获取安全管理器"""
    return security_manager


def decrypt_api_key(enc_text: str, iv: str) -> str:
    return security_manager.decrypt_api_key(enc_text, iv)
