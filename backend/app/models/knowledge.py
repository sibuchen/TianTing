"""
Knowledge Models
知识库文档表 + 文档分块表 + Q&A表
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pgvector.sqlalchemy import Vector

from app.models.base import BaseModel
from app.config import settings

if TYPE_CHECKING:
    from app.models.agent import AgentKnowledgeDocument, AgentKnowledgeQA


class KnowledgeDocument(BaseModel):
    """知识库文档表"""

    __tablename__ = "knowledge_documents"
    __table_args__ = (
        {"comment": "知识库文档表", "extend_existing": True},
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vector_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    vector_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    agent_links: Mapped[list["AgentKnowledgeDocument"]] = relationship(
        "AgentKnowledgeDocument",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(BaseModel):
    """文档分块与向量表"""

    __tablename__ = "document_chunks"
    __table_args__ = (
        {"comment": "文档分块与向量表（RAG检索核心表）", "extend_existing": True},
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(
        Vector(settings.embed_model_dimension or settings.embedding_dimension),
        nullable=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument",
        back_populates="chunks",
    )


class KnowledgeQA(BaseModel):
    """知识库Q&A表"""

    __tablename__ = "knowledge_qa"
    __table_args__ = (
        {"comment": "知识库Q&A表", "extend_existing": True},
    )

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(
        Vector(settings.embed_model_dimension or settings.embedding_dimension),
        nullable=True,
    )
    agent_links: Mapped[list["AgentKnowledgeQA"]] = relationship(
        "AgentKnowledgeQA",
        back_populates="qa",
        cascade="all, delete-orphan",
    )
