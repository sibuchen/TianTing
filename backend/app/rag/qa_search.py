"""
QA Search
问答检索：基于关键词和语义的Q&A检索
"""

import logging
from typing import Any

from sqlalchemy import select, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeQA
from app.rag.embedder import embedder
from app.rag.qdrant_client import qdrant_manager

logger = logging.getLogger(__name__)


class QASearch:
    """问答检索"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        搜索Q&A：向量优先 + ILIKE兜底
        """
        try:
            embeddings = await embedder.embed_text(query)
            query_embedding = embeddings[0]
        except Exception:
            logger.warning("Embedding failed, falling back to ILIKE search")
            return await self._keyword_search(query, limit)

        qdrant_results = await qdrant_manager.search_qa(
            query_embedding, limit=limit, threshold=threshold
        )
        if qdrant_results:
            return qdrant_results

        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        try:
            sql = text("""
                SELECT kq.question, kq.answer,
                       1 - (kq.embedding <=> :embedding :: vector) AS score
                FROM knowledge_qa kq
                WHERE kq.embedding IS NOT NULL
                  AND 1 - (kq.embedding <=> :embedding :: vector) >= :threshold
                ORDER BY kq.embedding <=> :embedding :: vector
                LIMIT :limit
            """)

            result = await self.db.execute(sql, {
                "embedding": embedding_str,
                "threshold": threshold,
                "limit": limit,
            })
            rows = result.fetchall()

            if rows:
                return [
                    {
                        "question": row.question,
                        "answer": row.answer,
                        "score": float(row.score) if row.score else 0.0,
                    }
                    for row in rows
                ]
        except Exception:
            logger.warning("Vector search failed, falling back to ILIKE search")

        return await self._keyword_search(query, limit)

    async def _keyword_search(
        self,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """ILIKE关键词双向匹配兜底"""
        conditions = [
            KnowledgeQA.question.ilike(f"%{query}%"),
            KnowledgeQA.answer.ilike(f"%{query}%"),
        ]

        result = await self.db.execute(
            select(KnowledgeQA)
            .where(or_(*conditions))
            .limit(limit)
        )

        qa_list = result.scalars().all()

        return [
            {
                "question": qa.question,
                "answer": qa.answer,
                "score": self._calculate_relevance(qa.question, qa.answer, query),
            }
            for qa in qa_list
        ]

    def _calculate_relevance(
        self, question: str, answer: str, query: str
    ) -> float:
        """计算相关性分数"""
        query_lower = query.lower()
        question_lower = question.lower()
        answer_lower = answer.lower()

        score = 0.0

        if query_lower in question_lower:
            score += 0.6
        if query_lower in answer_lower:
            score += 0.3
        if question_lower in query_lower:
            score += 0.6
        if answer_lower in query_lower:
            score += 0.3

        query_words = set(query_lower.split())
        question_words = set(question_lower.split())
        answer_words = set(answer_lower.split())

        overlap_question = len(query_words & question_words) / max(len(query_words), 1)
        overlap_answer = len(query_words & answer_words) / max(len(query_words), 1)

        score += overlap_question * 0.5 + overlap_answer * 0.2

        return min(score, 1.0)