"""
Knowledge API
知识库管理模块
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, BackgroundTasks

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_admin_user
from app.models.knowledge import KnowledgeDocument, KnowledgeQA
from app.rag.embedder import embedder
from app.schemas.knowledge import (
    DocumentListResponse,
    DocumentUploadResponse,
    DocumentPreviewResponse,
    QAItem,
    QAListResponse,
    QACreate,
    QAUpdate,
)
from app.schemas.common import BaseResponse, PaginatedResponse
from app.services.knowledge_service import KnowledgeService
from app.tasks.document_tasks import process_document_vectorization

router = APIRouter()


@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """获取文档列表"""
    service = KnowledgeService(db)
    documents, total = await service.get_documents(search, page, page_size)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return DocumentListResponse(
        data={
            "items": [
                {
                    "id": doc.id,
                    "fileName": doc.file_name,
                    "fileType": doc.file_type,
                    "fileSize": doc.file_size,
                    "vectorStatus": doc.vector_status,
                    "vectorProgress": doc.vector_progress,
                    "totalChunks": doc.total_chunks,
                    "processedChunks": doc.processed_chunks,
                    "createdAt": doc.created_at.isoformat() if doc.created_at else None,
                }
                for doc in documents
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    )


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """上传文档"""
    service = KnowledgeService(db)

    content = await file.read()
    document = await service.upload_document(
        file_name=file.filename or "unknown",
        file_content=content,
        file_size=len(content),
    )

    background_tasks.add_task(process_document_vectorization, document.id)

    return DocumentUploadResponse(
        message="文档上传成功，正在处理向量化",
        data={
            "id": document.id,
            "fileName": document.file_name,
            "fileSize": document.file_size,
            "vectorStatus": document.vector_status,
        },
    )


@router.delete("/documents/{document_id}", response_model=BaseResponse)
async def delete_document(
    document_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """删除文档"""
    service = KnowledgeService(db)
    await service.delete_document(document_id)
    return BaseResponse(message="删除成功")


@router.get("/documents/{document_id}/preview", response_model=BaseResponse)
async def preview_document(
    document_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """预览文档"""
    service = KnowledgeService(db)
    content, file_name, file_type = await service.get_document_preview(document_id)
    return BaseResponse(
        data={
            "content": content,
            "fileName": file_name,
            "fileType": file_type,
        }
    )


@router.post("/documents/{document_id}/retry", response_model=BaseResponse)
async def retry_vectorization(
    document_id: str,
    background_tasks: BackgroundTasks,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """重试向量化"""
    service = KnowledgeService(db)
    await service.retry_vectorization(document_id)
    background_tasks.add_task(process_document_vectorization, document_id)
    return BaseResponse(message="重试成功")


@router.get("/qa", response_model=QAListResponse)
async def get_qa_list(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> QAListResponse:
    """获取Q&A列表"""
    service = KnowledgeService(db)
    qa_list, total = await service.get_qa_list(search, page, page_size)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return QAListResponse(
        data={
            "items": [
                QAItem(
                    id=qa.id,
                    question=qa.question,
                    answer=qa.answer,
                    created_at=qa.created_at.isoformat() if qa.created_at else None,
                )
                for qa in qa_list
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    )


@router.post("/qa", response_model=BaseResponse)
async def create_qa(
    data: QACreate,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """创建Q&A"""
    service = KnowledgeService(db)
    qa = await service.create_qa(data.question, data.answer)
    return BaseResponse(data={"id": qa.id})


@router.put("/qa/{qa_id}", response_model=BaseResponse)
async def update_qa(
    qa_id: str,
    data: QAUpdate,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """更新Q&A"""
    service = KnowledgeService(db)
    await service.update_qa(qa_id, data.question, data.answer)
    return BaseResponse(message="更新成功")


@router.delete("/qa/{qa_id}", response_model=BaseResponse)
async def delete_qa(
    qa_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """删除Q&A"""
    service = KnowledgeService(db)
    await service.delete_qa(qa_id)
    return BaseResponse(message="删除成功")


@router.post("/qa/vectorize", response_model=BaseResponse)
async def vectorize_qa_batch(
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """批量向量化未处理的QA数据"""
    result = await db.execute(
        select(KnowledgeQA).where(KnowledgeQA.embedding == None)
    )
    qa_list = result.scalars().all()

    total = len(qa_list)
    success = 0
    failed = 0
    errors: list[str] = []

    for qa in qa_list:
        try:
            embeddings = await embedder.embed_text(qa.question)
            qa.embedding = embeddings[0]
            await db.commit()
            success += 1
        except Exception as e:
            await db.rollback()
            failed += 1
            errors.append(f"QA {qa.id}: {str(e)}")

    return BaseResponse(
        data={
            "total": total,
            "success": success,
            "failed": failed,
            "errors": errors,
        }
    )


@router.get("", response_model=BaseResponse)
async def get_knowledge_bases(
    search: str | None = Query(None),
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取知识库列表"""
    result = await db.execute(
        select(KnowledgeDocument)
    )
    documents = result.scalars().all()
    return BaseResponse(
        data=[
            {
                "id": doc.id,
                "fileName": doc.file_name,
                "fileType": doc.file_type,
                "fileSize": doc.file_size,
                "vectorStatus": doc.vector_status,
                "vectorProgress": doc.vector_progress,
                "createdAt": doc.created_at.isoformat() if doc.created_at else None,
            }
            for doc in documents
        ]
    )


@router.get("/{knowledge_id}", response_model=BaseResponse)
async def get_knowledge_base(
    knowledge_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """获取知识库详情"""
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == knowledge_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        return BaseResponse(code=404, message="知识库不存在")
    return BaseResponse(
        data={
            "id": doc.id,
            "fileName": doc.file_name,
            "fileType": doc.file_type,
            "fileSize": doc.file_size,
            "vectorStatus": doc.vector_status,
            "vectorProgress": doc.vector_progress,
            "totalChunks": doc.total_chunks,
            "processedChunks": doc.processed_chunks,
            "createdAt": doc.created_at.isoformat() if doc.created_at else None,
        }
    )


@router.post("", response_model=BaseResponse)
async def create_knowledge_base(
    data: dict,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """创建知识库"""
    doc = KnowledgeDocument(
        file_name=data.get("name", "New Knowledge Base"),
        file_type=data.get("type", "text"),
        file_size=0,
        vector_status="pending",
        vector_progress=0,
        total_chunks=0,
        processed_chunks=0,
    )
    db.add(doc)
    await db.commit()
    return BaseResponse(data={"id": doc.id})


@router.put("/{knowledge_id}", response_model=BaseResponse)
async def update_knowledge_base(
    knowledge_id: str,
    data: dict,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """更新知识库"""
    update_data = {}
    if "name" in data:
        update_data["file_name"] = data["name"]
    if update_data:
        await db.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.id == knowledge_id)
            .values(**update_data)
        )
        await db.commit()
    return BaseResponse(message="更新成功")


@router.delete("/{knowledge_id}", response_model=BaseResponse)
async def delete_knowledge_base(
    knowledge_id: str,
    admin_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse:
    """删除知识库"""
    await db.execute(
        delete(KnowledgeDocument).where(KnowledgeDocument.id == knowledge_id)
    )
    await db.commit()
    return BaseResponse(message="删除成功")
