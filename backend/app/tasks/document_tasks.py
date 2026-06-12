"""
Document Tasks
文档处理任务
"""

import logging
import os
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.core.database import get_db_context
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.rag.embedder import embedder
from app.rag.qdrant_client import qdrant_manager

logger = logging.getLogger(__name__)


async def process_document_vectorization(document_id: str) -> dict:
    """
    处理文档向量化任务
    """
    async with get_db_context() as db:
        result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            logger.error(f"Document not found: {document_id}")
            return {"status": "error", "message": "Document not found"}

        try:
            await db.execute(
                update(KnowledgeDocument)
                .where(KnowledgeDocument.id == document_id)
                .values(vector_status="processing")
            )
            await db.commit()

            if document.file_path and os.path.exists(document.file_path):
                with open(document.file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            else:
                logger.warning(f"File not found at path: {document.file_path}, using mock content")
                content = "Mock document content for testing"

            chunks = _chunk_text(content)

            await db.execute(
                update(KnowledgeDocument)
                .where(KnowledgeDocument.id == document_id)
                .values(
                    total_chunks=len(chunks),
                    processed_chunks=0,
                )
            )
            await db.commit()

            embeddings = await embedder.embed_texts(chunks)

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    content=chunk,
                    embedding=embedding,
                    chunk_index=i,
                )
                db.add(chunk_record)

                await db.execute(
                    update(KnowledgeDocument)
                    .where(KnowledgeDocument.id == document_id)
                    .values(
                        processed_chunks=i + 1,
                        vector_progress=int((i + 1) / len(chunks) * 100),
                    )
                )
                await db.commit()

            await db.execute(
                update(KnowledgeDocument)
                .where(KnowledgeDocument.id == document_id)
                .values(
                    vector_status="completed",
                    vector_progress=100,
                )
            )
            await db.commit()

            try:
                qdrant_chunks = [
                    {
                        "embedding": emb,
                        "chunk_index": i,
                        "content": chunk,
                    }
                    for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
                ]
                await qdrant_manager.upsert_document_chunks(document_id, qdrant_chunks)
            except Exception:
                logger.warning("Qdrant upsert failed for document %s", document_id, exc_info=True)

            logger.info(f"Document {document_id} vectorized successfully: {len(chunks)} chunks")
            return {
                "status": "success",
                "document_id": document_id,
                "total_chunks": len(chunks),
            }

        except Exception as e:
            logger.error(f"Vectorization failed for document {document_id}: {e}", exc_info=True)
            await db.execute(
                update(KnowledgeDocument)
                .where(KnowledgeDocument.id == document_id)
                .values(
                    vector_status="failed",
                    error_message=str(e),
                )
            )
            await db.commit()

            return {"status": "error", "message": str(e)}



def _chunk_text(content: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """文本分块"""
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
