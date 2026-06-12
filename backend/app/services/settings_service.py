"""
Settings Service
设置服务
"""

import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.setting import Setting
from app.config import settings


class SettingsService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_settings(self, user: User) -> dict:
        result = await self.db.execute(
            select(Setting)
        )
        settings_list = result.scalars().all()

        settings_map = {}
        for s in settings_list:
            if s.category not in settings_map:
                settings_map[s.category] = {}
            settings_map[s.category][s.key] = s.value

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "avatar": user.avatar,
            },
            "appearance": {
                "theme": settings_map.get("appearance", {}).get("theme", "light"),
                "language": settings_map.get("appearance", {}).get("language", "zh-CN"),
                "sidebarCollapsed": settings_map.get("appearance", {}).get(
                    "sidebarCollapsed", False
                ),
            },
            "notifications": {
                "emailEnabled": settings_map.get("notifications", {}).get(
                    "emailEnabled", True
                ),
                "soundEnabled": settings_map.get("notifications", {}).get(
                    "soundEnabled", True
                ),
                "desktopNotifications": settings_map.get("notifications", {}).get(
                    "desktopNotifications", True
                ),
            },
            "chatWidget": {
                "primaryColor": settings_map.get("chat_widget", {}).get(
                    "primaryColor", "#6366F1"
                ),
                "position": settings_map.get("chat_widget", {}).get("position", "right"),
                "welcomeMessage": settings_map.get("chat_widget", {}).get(
                    "welcomeMessage", "您好，有什么可以帮您？"
                ),
            },
            "about": {
                "version": settings_map.get("about", {}).get("version", "v1.0.0"),
                "buildDate": settings_map.get("about", {}).get(
                    "buildDate", "2025-01-01"
                ),
            },
        }

    async def update_settings(
        self,
        appearance: dict | None = None,
        notifications: dict | None = None,
        chat_widget: dict | None = None,
    ) -> None:
        """更新系统设置"""
        updates = [
            ("appearance", appearance),
            ("notifications", notifications),
            ("chat_widget", chat_widget),
        ]

        for category, data in updates:
            if data:
                for key, value in data.items():
                    result = await self.db.execute(
                        select(Setting).where(
                            Setting.category == category,
                            Setting.key == key,
                        )
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        await self.db.execute(
                            update(Setting)
                            .where(Setting.id == existing.id)
                            .values(value=value)
                        )
                    else:
                        new_setting = Setting(
                            category=category,
                            key=key,
                            value=value,
                        )
                        self.db.add(new_setting)

        await self.db.commit()

    async def upload_avatar(self, user_id: str, file_content, filename: str) -> str:
        """上传头像"""
        avatar_dir = os.path.join(settings.upload_dir, "avatars")
        os.makedirs(avatar_dir, exist_ok=True)

        avatar_filename = f"{user_id}_{uuid.uuid4().hex[:8]}_{filename}"
        avatar_path = os.path.join(avatar_dir, avatar_filename)

        with open(avatar_path, "wb") as f:
            f.write(file_content)

        avatar_url = f"/uploads/avatars/{avatar_filename}"

        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(avatar=avatar_url)
        )
        await self.db.commit()

        return avatar_url

    async def check_update(self) -> dict:
        """检查系统更新"""
        return {
            "currentVersion": settings.app_version,
            "latestVersion": settings.app_version,
            "hasUpdate": False,
            "releaseNotes": "",
        }
