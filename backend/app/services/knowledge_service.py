"""
Knowledge Service
知识库服务：文档管理/检索
"""

import logging
import os
import uuid

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    DocumentNotFoundError,
)
from app.models.knowledge import KnowledgeDocument, DocumentChunk, KnowledgeQA
from app.config import settings
from app.rag.qdrant_client import qdrant_manager

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_documents(
        self, search: str | None = None, page: int = 1, page_size: int = 12
    ) -> tuple[list[KnowledgeDocument], int]:
        """获取文档列表"""
        query = select(KnowledgeDocument)

        if search:
            query = query.where(
                KnowledgeDocument.file_name.ilike(f"%{search}%")
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(KnowledgeDocument.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        documents = list(result.scalars().all())

        return documents, total

    async def upload_document(
        self,
        file_name: str,
        file_content: bytes,
        file_size: int,
    ) -> KnowledgeDocument:
        """上传文档"""
        file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

        if file_ext not in settings.allowed_file_types:
            raise UnsupportedFileTypeError()

        if file_size > settings.max_upload_size:
            raise FileTooLargeError()

        os.makedirs(settings.upload_dir, exist_ok=True)
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.upload_dir, f"{file_id}_{file_name}")

        with open(file_path, "wb") as f:
            f.write(file_content)

        document = KnowledgeDocument(
            id=file_id,
            file_name=file_name,
            file_type=file_ext,
            file_size=file_size,
            file_path=file_path,
            vector_status="pending",
            vector_progress=0,
        )
        self.db.add(document)
        await self.db.commit()

        await self.db.refresh(document)

        return document

    async def delete_document(self, document_id: str) -> None:
        """删除文档"""
        result = await self.db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundError()

        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)

        await self.db.execute(
            delete(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )

        await self.db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document_id
            )
        )

        await self.db.commit()

    async def get_document_preview(self, document_id: str) -> tuple[str, str, str]:
        """预览文档"""
        result = await self.db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundError()

        content = ""
        if document.file_path and os.path.exists(document.file_path):
            with open(document.file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)

        return content, document.file_name, document.file_type

    async def retry_vectorization(self, document_id: str) -> None:
        """重试向量化"""
        result = await self.db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundError()

        await self.db.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.id == document_id)
            .values(
                vector_status="pending",
                vector_progress=0,
                error_message=None,
            )
        )
        await self.db.commit()

    async def get_qa_list(
        self, search: str | None = None, page: int = 1, page_size: int = 10
    ) -> tuple[list[KnowledgeQA], int]:
        """获取Q&A列表"""
        query = select(KnowledgeQA)

        if search:
            query = query.where(
                KnowledgeQA.question.ilike(f"%{search}%")
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(KnowledgeQA.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        qa_list = list(result.scalars().all())

        return qa_list, total

    async def create_qa(self, question: str, answer: str) -> KnowledgeQA:
        """创建Q&A"""
        qa = KnowledgeQA(question=question, answer=answer)
        self.db.add(qa)
        await self.db.commit()
        await self.db.refresh(qa)

        try:
            from app.rag.embedder import embedder
            embeddings = await embedder.embed_text(question)
            qa.embedding = embeddings[0]
            await self.db.commit()
            await self.db.refresh(qa)
            await qdrant_manager.upsert_qa(str(qa.id), question, answer, embeddings[0])
        except Exception as e:
            logger.error(f"Failed to embed QA question: {e}")

        return qa

    async def update_qa(self, qa_id: str, question: str, answer: str) -> None:
        """更新Q&A"""
        result = await self.db.execute(
            select(KnowledgeQA).where(KnowledgeQA.id == qa_id)
        )
        qa = result.scalar_one_or_none()

        if not qa:
            raise DocumentNotFoundError()

        question_changed = qa.question != question

        await self.db.execute(
            update(KnowledgeQA)
            .where(KnowledgeQA.id == qa_id)
            .values(question=question, answer=answer)
        )
        await self.db.commit()

        if question_changed:
            try:
                from app.rag.embedder import embedder
                embeddings = await embedder.embed_text(question)
                await self.db.execute(
                    update(KnowledgeQA)
                    .where(KnowledgeQA.id == qa_id)
                    .values(embedding=embeddings[0])
                )
                await self.db.commit()
                await qdrant_manager.upsert_qa(qa_id, question, answer, embeddings[0])
            except Exception as e:
                logger.error(f"Failed to re-embed QA question: {e}")

    async def delete_qa(self, qa_id: str) -> None:
        """删除Q&A"""
        result = await self.db.execute(
            select(KnowledgeQA).where(KnowledgeQA.id == qa_id)
        )
        qa = result.scalar_one_or_none()

        if not qa:
            raise DocumentNotFoundError()

        await self.db.execute(
            delete(KnowledgeQA).where(KnowledgeQA.id == qa_id)
        )
        await self.db.commit()

        await qdrant_manager.delete_qa(qa_id)
