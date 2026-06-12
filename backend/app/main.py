"""
TianTing Application
FastAPI应用入口 + lifespan事件管理
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware

from app.config import settings
from app.core.database import init_database, close_database
from app.core.redis import redis_manager
from app.core.security import security_manager
from app.core.middleware import (
    setup_cors,
    setup_exception_handlers,
    request_logging_middleware,
    non_ascii_url_middleware,
)
from app.api.router import api_router
from app.ws.manager import manager
from app.core.token_store import token_store
from app.rag.qdrant_client import qdrant_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    init_database()
    await redis_manager.init()
    qdrant_manager.init()
    security_manager.init()
    token_store.init()

    from app.graph.neo4j_client import neo4j_manager
    await neo4j_manager.init()

    from app.services.mongo_client import mongo_client
    await mongo_client.init()

    if neo4j_manager.enabled:
        from app.core.database import get_db_context
        from app.graph.sync_service import graph_sync_service
        async with get_db_context() as db:
            await graph_sync_service.full_sync(db)

    os.makedirs(settings.upload_dir, exist_ok=True)

    if settings.feishu_enabled and settings.feishu_event_mode == "websocket":
        from app.im.feishu.ws_client import start_ws_client
        start_ws_client()

    yield

    if settings.feishu_enabled and settings.feishu_event_mode == "websocket":
        from app.im.feishu.ws_client import stop_ws_client
        stop_ws_client()

    await neo4j_manager.close()
    await qdrant_manager.close()
    await redis_manager.close()
    await mongo_client.close()
    await close_database()


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="天听（TianTing）智能客服系统后端API",
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )

    setup_cors(app)
    setup_exception_handlers(app)

    app.middleware("http")(request_logging_middleware)
    app.middleware("http")(non_ascii_url_middleware)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    from app.api.analytics import router as analytics_router
    app.include_router(analytics_router)

    if os.path.exists(settings.upload_dir):
        app.mount(
            "/uploads",
            StaticFiles(directory=settings.upload_dir),
            name="uploads",
        )

    @app.websocket("/ws/admin")
    async def admin_websocket(websocket):
        """Admin WebSocket"""
        from app.ws.manager import WebSocketHandler

        handler = WebSocketHandler(manager)
        await handler.handle_admin_connection(websocket)

    @app.websocket("/ws/chat/{session_id}")
    async def chat_websocket(websocket, session_id: str):
        """Chat WebSocket"""
        from app.ws.manager import WebSocketHandler

        handler = WebSocketHandler(manager)
        await handler.handle_chat_connection(websocket, session_id)

    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.debug,
    )
