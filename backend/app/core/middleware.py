"""
Middleware
中间件：CORS/速率限制/错误处理
"""

from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.core.exceptions import TiantingException


def create_limiter() -> Limiter:
    """创建限流器"""
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.redis_url,
        default_limits=["60/minute"],
    )
    return limiter


def setup_cors(app: FastAPI) -> None:
    """设置CORS"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """设置异常处理器"""

    @app.exception_handler(TiantingException)
    async def tianting_exception_handler(
        request: Request, exc: TiantingException
    ) -> JSONResponse:
        """天听异常处理器"""
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(
        request: Request, exc: RateLimitExceeded
    ) -> JSONResponse:
        """速率限制异常处理器"""
        return JSONResponse(
            status_code=429,
            content={
                "code": 429,
                "message": "请求过于频繁",
                "details": {},
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """通用异常处理器"""
        if settings.debug:
            import traceback

            return JSONResponse(
                status_code=500,
                content={
                    "code": 99999,
                    "message": str(exc),
                    "details": {"traceback": traceback.format_exc()},
                },
            )
        return JSONResponse(
            status_code=500,
            content={
                "code": 99999,
                "message": "服务器内部错误",
                "details": {},
            },
        )


async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    """请求日志中间件"""
    import time

    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    return response


async def non_ascii_url_middleware(request: Request, call_next: Callable) -> Response:
    """非ASCII URL兼容中间件

    当请求URL中包含未编码的非ASCII字符时，Uvicorn的HTTP解析器会直接断开连接，
    导致客户端收到不可读的错误信息。此中间件在Starlette层面捕获此类请求，
    返回友好的400错误，提示客户端对URL进行编码。
    """
    try:
        raw_path = str(request.url)
        raw_path.encode("ascii")
    except UnicodeEncodeError:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": "请求URL包含非ASCII字符，请对URL进行编码后重试（如中文需URL Encoding）",
                "details": {
                    "hint": "浏览器会自动处理URL编码，此问题通常仅出现在直接API调用时"
                },
            },
        )

    return await call_next(request)
