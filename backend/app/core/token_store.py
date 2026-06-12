"""
Token Store
Token 加密文件存储：将 JWT 加密存储在 ~/.tianting/{session_id}.enc
Windows 自动适配 %USERPROFILE%\\.tianting
"""

import base64
import os
import platform
import secrets
import stat
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


def _get_token_store_dir() -> Path:
    if settings.token_store_dir:
        return Path(settings.token_store_dir)
    if platform.system() == "Windows":
        base = Path(os.environ.get("USERPROFILE", Path.home()))
    else:
        base = Path.home()
    return base / ".tianting"


class TokenStore:
    def __init__(self) -> None:
        self._store_dir: Path | None = None
        self._aesgcm: AESGCM | None = None

    def init(self) -> None:
        self._store_dir = _get_token_store_dir()
        self._store_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(str(self._store_dir), stat.S_IRWXU)
        except OSError:
            pass

        key = settings.encryption_key.encode("utf-8")
        if len(key) != 32:
            import hashlib
            key = hashlib.sha256(key).digest()
        self._aesgcm = AESGCM(key)

    @property
    def aesgcm(self) -> AESGCM:
        if self._aesgcm is None:
            raise RuntimeError("TokenStore not initialized")
        return self._aesgcm

    @property
    def store_dir(self) -> Path:
        if self._store_dir is None:
            raise RuntimeError("TokenStore not initialized")
        return self._store_dir

    def _session_file(self, session_id: str) -> Path:
        return self.store_dir / f"{session_id}.enc"

    def save_token(self, token: str) -> str:
        session_id = secrets.token_urlsafe(32)
        iv = secrets.token_bytes(12)
        encrypted = self.aesgcm.encrypt(iv, token.encode("utf-8"), None)
        payload = base64.b64encode(iv) + b"." + base64.b64encode(encrypted)
        self._session_file(session_id).write_bytes(payload)
        return session_id

    def load_token(self, session_id: str) -> str | None:
        file_path = self._session_file(session_id)
        if not file_path.exists():
            return None
        try:
            payload = file_path.read_bytes()
            iv_b64, encrypted_b64 = payload.split(b".", 1)
            iv = base64.b64decode(iv_b64)
            encrypted = base64.b64decode(encrypted_b64)
            decrypted = self.aesgcm.decrypt(iv, encrypted, None)
            return decrypted.decode("utf-8")
        except Exception:
            return None

    def delete_token(self, session_id: str) -> bool:
        file_path = self._session_file(session_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False


token_store = TokenStore()


def get_token_store() -> TokenStore:
    return token_store
