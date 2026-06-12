"""
API Router
顶层路由注册
"""

from fastapi import APIRouter

from app.api.admin import auth, dashboard, agents, tools, skills, knowledge, human_service, history, users, settings, api_keys
from app.api.chat import sessions, messages
from app.im.feishu.webhook import router as feishu_router

api_router = APIRouter()

api_router.include_router(auth, prefix="/auth", tags=["认证模块"])
api_router.include_router(dashboard, prefix="/dashboard", tags=["仪表盘模块"])
api_router.include_router(agents, prefix="/agents", tags=["Agent管理"])
api_router.include_router(tools, prefix="/tools", tags=["工具管理"])
api_router.include_router(skills, prefix="/skills", tags=["Skills管理"])
api_router.include_router(knowledge, prefix="/knowledge", tags=["知识库管理"])
api_router.include_router(human_service, prefix="/human-service", tags=["人工客服"])
api_router.include_router(history, prefix="/history", tags=["历史记录"])
api_router.include_router(users, prefix="/users", tags=["用户管理"])
api_router.include_router(settings, prefix="/settings", tags=["系统设置"])
api_router.include_router(api_keys, prefix="/api-keys", tags=["API密钥管理"])
api_router.include_router(sessions, prefix="/chat/sessions", tags=["聊天会话"])
api_router.include_router(messages, prefix="/chat/sessions", tags=["聊天消息"])
api_router.include_router(feishu_router, prefix="/feishu", tags=["飞书IM"])
