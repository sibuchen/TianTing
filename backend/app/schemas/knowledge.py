"""
Knowledge Schemas
知识库相关
"""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import to_camel


class DocumentItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    file_name: str
    file_type: str
    file_size: int
    vector_status: str
    vector_progress: int
    total_chunks: int
    processed_chunks: int
    uploaded_at: str | None = None


class DocumentListData(BaseModel):

    items: list[DocumentItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentListResponse(BaseModel):

    code: int = 0
    data: DocumentListData


class DocumentUploadResponse(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "code": 0,
        "message": "文档上传成功，正在处理向量化",
        "data": {
            "id": "doc_001",
            "file_name": "产品手册.pdf",
            "file_size": 2048576,
            "vector_status": "processing"
        }
    }}, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    message: str = "文档上传成功，正在处理向量化"
    data: dict


class DocumentPreviewResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    content: str
    file_name: str
    file_type: str


class QAItem(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
    question: str
    answer: str
    created_at: str | None = None


class QAListData(BaseModel):

    items: list[QAItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class QAListResponse(BaseModel):

    code: int = 0
    data: QAListData


class QACreate(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "question": "如何退换货？",
        "answer": "您可以在收到商品后7天内申请退换货，请在订单详情页点击'申请退换货'按钮。"
    }}, alias_generator=to_camel, populate_by_name=True)

    question: str = Field(..., max_length=1000)
    answer: str = Field(..., max_length=5000)


class QAUpdate(BaseModel):

    model_config = ConfigDict(json_schema_extra={"example": {
        "question": "退换货的流程是什么？",
        "answer": "您可以在收到商品后7天内申请退换货，请在订单详情页点击'申请退换货'按钮，填写退换原因后提交即可。"
    }}, alias_generator=to_camel, populate_by_name=True)

    question: str = Field(..., max_length=1000)
    answer: str = Field(..., max_length=5000)


class QACreateResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    id: str
