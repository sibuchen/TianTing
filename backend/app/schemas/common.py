"""
Common Schemas
通用响应模型
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    message: str = "success"
    data: T | None = None


class PaginatedData(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 12
    total_pages: int = 0


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    message: str = "success"
    data: PaginatedData[T] | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int
    message: str
    details: dict[str, Any] = {}


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    message: str = "success"
    data: str | None = None


class IDResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    message: str = "success"
    data: dict[str, str] | None = None


class BoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    code: int = 0
    message: str = "success"
    data: bool | None = None
