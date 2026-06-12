"""
Retriever
检索器：基于 pgvector 的向量相似度检索
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.rag.qdrant_client import qdrant_manager

logger = logging.getLogger(__name__)


class Retriever:
    """检索器"""

    def __init__(self) -> None:
        self.top_k = settings.retrieval_top_k

    async def similarity_search(
        self,
        db: AsyncSession,
        query_embedding: list[float],
        limit: int | None = None,
        threshold: float = 0.7,
        doc_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        向量相似度检索 — 基于 pgvector cosine_distance
        返回相关文档块
        """
        qdrant_results = await qdrant_manager.search_documents(
            query_embedding, limit=limit or self.top_k, threshold=threshold
        )
        if qdrant_results:
            return qdrant_results

        limit = limit or self.top_k

        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        sql = text("""
            SELECT
                dc.content,
                1 - (dc.embedding <=> :embedding :: vector) AS score,
                dc.document_id,
                dc.chunk_index,
                dc.metadata
            FROM document_chunks dc
            WHERE dc.embedding IS NOT NULL
            AND 1 - (dc.embedding <=> :embedding :: vector) >= :threshold
            ORDER BY dc.embedding <=> :embedding :: vector
            LIMIT :limit
        """)

        params = {
            "embedding": embedding_str,
            "threshold": threshold,
            "limit": limit,
        }

        result = await db.execute(sql, params)
        rows = result.fetchall()

        results = []
        for row in rows:
            content, score, document_id, chunk_index, metadata = row
            if doc_ids and document_id not in doc_ids:
                continue
            results.append({
                "content": content,
                "score": float(score) if score else 0.0,
                "source": f"chunk_{chunk_index}",
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    **(metadata or {}),
                },
            })

        return results

    async def hybrid_search(
        self,
        db: AsyncSession,
        query: str,
        query_embedding: list[float] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        混合检索：结合语义相似度和关键词匹配
        """
        if query_embedding is None:
            from app.rag.embedder import embedder

            embeddings = await embedder.embed_text(query)
            query_embedding = embeddings[0] if embeddings else []

        return await self.similarity_search(db, query_embedding, limit)

    def rerank(
        self,
        results: list[dict[str, Any]],
        query: str,
    ) -> list[dict[str, Any]]:
        """
        重排序结果 — 按 score 降序
        """
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)


retriever = Retriever()