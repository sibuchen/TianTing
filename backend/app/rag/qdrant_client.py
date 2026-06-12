"""
Qdrant Vector Database Client
Qdrant向量数据库客户端
"""

import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantManager:

    def __init__(self) -> None:
        self._client: QdrantClient | None = None
        self._enabled = settings.qdrant_enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def init(self) -> None:
        if not self._enabled:
            logger.info("Qdrant is disabled, skipping initialization")
            return
        try:
            self._client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=30,
            )
            self._ensure_collections()
            logger.info("Qdrant initialized successfully at %s", settings.qdrant_url)
        except Exception:
            logger.warning("Failed to initialize Qdrant, disabling", exc_info=True)
            self._enabled = False
            self._client = None

    async def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def _collection_name(self, name: str) -> str:
        return f"{settings.qdrant_collection_prefix}_{name}"

    def _ensure_collections(self) -> None:
        dimension = settings.embed_model_dimension or settings.embedding_dimension
        collections = ["document_chunks", "knowledge_qa"]
        for name in collections:
            col_name = self._collection_name(name)
            try:
                self._client.get_collection(col_name)
            except Exception:
                self._client.create_collection(
                    collection_name=col_name,
                    vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
                )
                logger.info("Created Qdrant collection: %s", col_name)

    async def upsert_document_chunks(
        self,
        document_id: str,
        chunks: list[dict],
    ) -> bool:
        if not self._enabled or not self._client:
            return False
        try:
            col_name = self._collection_name("document_chunks")
            points = []
            for chunk in chunks:
                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=chunk["embedding"],
                    payload={
                        "document_id": document_id,
                        "chunk_index": chunk["chunk_index"],
                        "content": chunk["content"],
                    },
                ))
            self._client.upsert(collection_name=col_name, points=points)
            return True
        except Exception:
            logger.warning("Qdrant upsert_document_chunks failed", exc_info=True)
            return False

    async def upsert_qa(
        self,
        qa_id: str,
        question: str,
        answer: str,
        embedding: list[float],
    ) -> bool:
        if not self._enabled or not self._client:
            return False
        try:
            col_name = self._collection_name("knowledge_qa")
            self._client.upsert(
                collection_name=col_name,
                points=[
                    PointStruct(
                        id=qa_id,
                        vector=embedding,
                        payload={
                            "qa_id": qa_id,
                            "question": question,
                            "answer": answer,
                        },
                    )
                ],
            )
            return True
        except Exception:
            logger.warning("Qdrant upsert_qa failed", exc_info=True)
            return False

    async def delete_document_chunks(self, document_id: str) -> bool:
        if not self._enabled or not self._client:
            return False
        try:
            col_name = self._collection_name("document_chunks")
            self._client.delete(
                collection_name=col_name,
                points_selector=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                ),
            )
            return True
        except Exception:
            logger.warning("Qdrant delete_document_chunks failed", exc_info=True)
            return False

    async def delete_qa(self, qa_id: str) -> bool:
        if not self._enabled or not self._client:
            return False
        try:
            col_name = self._collection_name("knowledge_qa")
            self._client.delete(
                collection_name=col_name,
                points_selector=Filter(
                    must=[FieldCondition(key="qa_id", match=MatchValue(value=qa_id))]
                ),
            )
            return True
        except Exception:
            logger.warning("Qdrant delete_qa failed", exc_info=True)
            return False

    async def search_documents(
        self,
        query_embedding: list[float],
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        if not self._enabled or not self._client:
            return []
        try:
            col_name = self._collection_name("document_chunks")
            results = self._client.search(
                collection_name=col_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=threshold,
            )
            return [
                {
                    "content": hit.payload.get("content", ""),
                    "score": hit.score,
                    "source": f"chunk_{hit.payload.get('chunk_index', 0)}",
                    "metadata": {
                        "document_id": hit.payload.get("document_id", ""),
                        "chunk_index": hit.payload.get("chunk_index", 0),
                    },
                }
                for hit in results
            ]
        except Exception:
            logger.warning("Qdrant search_documents failed", exc_info=True)
            return []

    async def search_qa(
        self,
        query_embedding: list[float],
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        if not self._enabled or not self._client:
            return []
        try:
            col_name = self._collection_name("knowledge_qa")
            results = self._client.search(
                collection_name=col_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=threshold,
            )
            return [
                {
                    "question": hit.payload.get("question", ""),
                    "answer": hit.payload.get("answer", ""),
                    "score": hit.score,
                }
                for hit in results
            ]
        except Exception:
            logger.warning("Qdrant search_qa failed", exc_info=True)
            return []


qdrant_manager = QdrantManager()