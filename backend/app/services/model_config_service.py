"""
Model Config Service
模型配置服务：API Key管理
"""

import time
from datetime import datetime, timezone

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_security_manager
from app.core.exceptions import (
    ModelConfigInUseError,
    ModelAPIConnectionError,
    MCPServerConnectionError,
)
from app.models.model_config import ModelConfig
from app.models.agent import Agent


class ModelConfigService:
    """模型配置服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.security = get_security_manager()

    async def get_configs(self) -> list[ModelConfig]:
        """获取模型配置列表"""
        result = await self.db.execute(
            select(ModelConfig)
            .options(selectinload(ModelConfig.agents))
            .order_by(ModelConfig.created_at.desc())
        )
        return list(result.scalars().all())

    def mask_api_key(self, api_key: str) -> str:
        """掩码API Key"""
        return self.security.mask_api_key(api_key)

    async def create_config(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model_id: str,
    ) -> ModelConfig:
        """创建模型配置"""
        encrypted_key, iv = self.security.encrypt_api_key(api_key)

        config = ModelConfig(
            name=name,
            base_url=base_url,
            api_key_enc=encrypted_key,
            api_key_iv=iv,
            model_id=model_id,
            status="normal",
        )
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)

        return config

    async def update_config(
        self,
        config_id: str,
        name: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        model_id: str | None = None,
    ) -> None:
        """更新模型配置"""
        update_data = {}

        if name:
            update_data["name"] = name
        if base_url:
            update_data["base_url"] = base_url
        if model_id:
            update_data["model_id"] = model_id
        if api_key:
            encrypted_key, iv = self.security.encrypt_api_key(api_key)
            update_data["api_key_enc"] = encrypted_key
            update_data["api_key_iv"] = iv

        if update_data:
            await self.db.execute(
                update(ModelConfig)
                .where(ModelConfig.id == config_id)
                .values(**update_data)
            )
            await self.db.commit()

    async def delete_config(self, config_id: str) -> None:
        """删除模型配置"""
        result = await self.db.execute(
            select(Agent).where(Agent.model_config_id == config_id)
        )
        bound_agents = result.scalars().all()

        if bound_agents:
            raise ModelConfigInUseError()

        await self.db.execute(
            delete(ModelConfig).where(ModelConfig.id == config_id)
        )
        await self.db.commit()

    @staticmethod
    def _normalize_chat_url(base_url: str) -> str:
        url = base_url.rstrip("/")
        if url.endswith("/chat/completions"):
            return url
        return f"{url}/chat/completions"

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        url = base_url.rstrip("/")
        if url.endswith("/chat/completions"):
            url = url[:-len("/chat/completions")]
        return url

    async def test_config(self, config_id: str) -> dict:
        """测试模型配置"""
        result = await self.db.execute(
            select(ModelConfig).where(ModelConfig.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise ModelAPIConnectionError()

        start_time = time.time()

        try:
            decrypted_key = self.security.decrypt_api_key(
                config.api_key_enc, config.api_key_iv
            )

            import httpx

            headers = {
                "Authorization": f"Bearer {decrypted_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": config.model_id,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            }

            chat_url = self._normalize_chat_url(config.base_url)

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    chat_url,
                    headers=headers,
                    json=payload,
                )

            latency = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                await self.db.execute(
                    update(ModelConfig)
                    .where(ModelConfig.id == config_id)
                    .values(
                        status="normal",
                        last_tested_at=datetime.now(timezone.utc),
                    )
                )
                await self.db.commit()

                return {
                    "status": "normal",
                    "latency": latency,
                    "model_info": {
                        "provider": "OpenAI",
                        "model": config.model_id,
                        "capabilities": ["chat", "function_calling", "vision"],
                        "context_window": 128000,
                    },
                }
            elif response.status_code == 401:
                error_text = response.text[:200]
                await self.db.execute(
                    update(ModelConfig)
                    .where(ModelConfig.id == config_id)
                    .values(
                        status="error",
                        last_tested_at=datetime.now(timezone.utc),
                    )
                )
                await self.db.commit()
                raise ModelAPIConnectionError(detail=f"401 Unauthorized - {error_text}")
            else:
                error_text = response.text[:200]
                await self.db.execute(
                    update(ModelConfig)
                    .where(ModelConfig.id == config_id)
                    .values(
                        status="error",
                        last_tested_at=datetime.now(timezone.utc),
                    )
                )
                await self.db.commit()
                raise ModelAPIConnectionError(detail=f"HTTP {response.status_code} - {error_text}")

        except (ModelAPIConnectionError, MCPServerConnectionError):
            raise
        except Exception as e:
            await self.db.execute(
                update(ModelConfig)
                .where(ModelConfig.id == config_id)
                .values(
                    status="error",
                    last_tested_at=datetime.now(timezone.utc),
                )
            )
            await self.db.commit()
            raise ModelAPIConnectionError()
