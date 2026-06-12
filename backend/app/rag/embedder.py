"""
Embedder
向量化器：调用Embedding API生成向量
"""

import os
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class Embedder:
    """向量化器"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.embed_model_api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or settings.embed_model_base_url or os.getenv("OPENAI_API_BASE", "https://api.openai.com")
        self.model = model or settings.embed_model_id or settings.embedding_model
        self.dimension = settings.embed_model_dimension or settings.embedding_dimension
        self._use_mock = os.getenv("MOCK_EMBEDDING", "false").lower() == "true"

    async def embed_text(self, text: str) -> list[float]:
        """单条文本向量化"""
        return await self._embed([text])

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化"""
        return await self._embed(texts)

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        """调用Embedding API"""
        if self._use_mock:
            logger.warning("Using mock embeddings (MOCK_EMBEDDING=true)")
            return self._generate_mock_embeddings(len(texts))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": texts,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    result = response.json()
                    return [item["embedding"] for item in result["data"]]
                else:
                    raise RuntimeError(
                        f"Embedding API returned status {response.status_code}: {response.text[:200]}"
                    )

        except httpx.HTTPError as e:
            raise RuntimeError(f"Embedding API request failed: {e}") from e

    def _generate_mock_embeddings(self, count: int) -> list[list[float]]:
        """生成模拟向量（用于测试）"""
        import random

        return [
            [random.uniform(-1, 1) for _ in range(self.dimension)]
            for _ in range(count)
        ]

    async def embed_document(self, content: str) -> list[list[float]]:
        """文档向量化"""
        chunks = self._chunk_text(content)
        return await self.embed_texts(chunks)

    def _chunk_text(
        self, content: str, chunk_size: int | None = None, overlap: int | None = None
    ) -> list[str]:
        """文本分块"""
        chunk_size = chunk_size or settings.chunk_size
        overlap = overlap or settings.chunk_overlap

        if len(content) <= chunk_size:
            return [content]

        chunks = []
        start = 0

        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            chunks.append(chunk)
            start = end - overlap

        return chunks


embedder = Embedder()
