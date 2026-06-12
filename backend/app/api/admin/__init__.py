"""
Admin Package
管理后台API
"""

from app.api.admin.auth import router as auth
from app.api.admin.dashboard import router as dashboard
from app.api.admin.agents import router as agents
from app.api.admin.tools import router as tools
from app.api.admin.skills import router as skills
from app.api.admin.knowledge import router as knowledge
from app.api.admin.human_service import router as human_service
from app.api.admin.history import router as history
from app.api.admin.users import router as users
from app.api.admin.api_keys import router as api_keys
from app.api.admin.settings import router as settings

__all__ = [
    "auth",
    "dashboard",
    "agents",
    "tools",
    "skills",
    "knowledge",
    "human_service",
    "history",
    "users",
    "api_keys",
    "settings",
]
