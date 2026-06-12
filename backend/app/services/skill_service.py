"""
Skill Service
技能服务：CRUD + 技能测试（调用LLM）+ 导入导出
"""

import io
import logging
import mimetypes
import os
import re
import shutil
import time
import zipfile

import httpx
import yaml
from sqlalchemy import or_, select, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    SkillNotFoundError,
    SkillBuiltinModifyError,
    SkillInUseError,
    NoModelAvailableError,
)
from app.core.security import get_security_manager
from app.models.skill import Skill, SkillResource
from app.models.agent import AgentSkill
from app.models.model_config import ModelConfig
from app.schemas.skill import SkillCreate, SkillUpdate

logger = logging.getLogger(__name__)


class SkillService:
    """技能服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_skills(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Skill]:
        """获取技能列表（内置+自定义），支持筛选"""
        stmt = select(Skill).options(selectinload(Skill.resources))

        if category:
            stmt = stmt.where(Skill.category == category)

        if tags:
            tag_conditions = [Skill.tags.op("?")(tag) for tag in tags]
            stmt = stmt.where(or_(*tag_conditions))

        if status:
            stmt = stmt.where(Skill.status == status)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                (Skill.name.ilike(search_term))
                | (Skill.display_name.ilike(search_term))
                | (Skill.description.ilike(search_term))
                | (Skill.skill_body.ilike(search_term))
                | (Skill.prompts.ilike(search_term))
            )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_tags(self) -> list[str]:
        """获取所有技能中使用过的标签（去重）"""
        result = await self.db.execute(
            text(
                "SELECT DISTINCT jsonb_array_elements_text(tags) AS tag "
                "FROM skills WHERE tags IS NOT NULL AND jsonb_array_length(tags) > 0"
            )
        )
        return [row[0] for row in result.fetchall()]

    async def create_skill(self, data: SkillCreate) -> Skill:
        """创建自定义技能"""
        skill = Skill(
            name=data.name,
            display_name=data.display_name,
            icon=data.icon,
            icon_color=data.icon_color,
            category=data.category,
            description=data.description,
            status="active",
            tags=data.tags,
            skill_body=data.skill_body,
            version=data.version,
            author=data.author,
            prompts=data.prompts,
            is_builtin=False,
        )
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def update_skill(self, skill_id: str, data: SkillUpdate) -> None:
        """更新技能（仅允许修改非内置技能）"""
        result = await self.db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = result.scalar_one_or_none()

        if not skill:
            raise SkillNotFoundError()

        if skill.is_builtin:
            raise SkillBuiltinModifyError()

        update_data = data.model_dump(exclude_unset=True)

        if update_data:
            await self.db.execute(
                update(Skill)
                .where(Skill.id == skill_id)
                .values(**update_data)
            )
            await self.db.commit()

    async def delete_skill(self, skill_id: str) -> None:
        """删除技能（仅允许删除非内置技能）"""
        result = await self.db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = result.scalar_one_or_none()

        if not skill:
            raise SkillNotFoundError()

        if skill.is_builtin:
            raise SkillBuiltinModifyError()

        agent_result = await self.db.execute(
            select(AgentSkill).where(AgentSkill.skill_id == skill_id)
        )
        if agent_result.scalars().first():
            raise SkillInUseError()

        await self.db.execute(
            delete(AgentSkill).where(AgentSkill.skill_id == skill_id)
        )
        await self.db.execute(
            delete(Skill).where(Skill.id == skill_id)
        )
        await self.db.commit()

        # Clean up resource files from disk
        skill_dir = os.path.join("uploads", "skills", skill_id)
        if os.path.exists(skill_dir):
            shutil.rmtree(skill_dir)

    async def test_skill(self, skill_id: str) -> dict:
        """测试技能执行（调用LLM获取真实响应）"""
        result = await self.db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = result.scalar_one_or_none()

        if not skill:
            raise SkillNotFoundError()

        model_config = await self._get_available_model()
        if not model_config:
            raise NoModelAvailableError()

        system_prompt = skill.prompts or f"你是{skill.name}助手，请根据用户的需求提供帮助。"
        display = skill.display_name or skill.name
        trigger = skill.description or f"使用{display}功能"
        user_message = f"我想{trigger}"

        start_time = time.time()

        try:
            response_content = await self._call_llm(
                model_config=model_config,
                system_prompt=system_prompt,
                user_message=user_message,
            )
            execution_time = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "result": response_content,
                "executionTime": execution_time,
                "modelUsed": model_config.name,
                "skillName": skill.name,
            }
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "result": f"LLM调用失败: {str(e)}",
                "executionTime": execution_time,
                "modelUsed": model_config.name,
                "skillName": skill.name,
            }

    async def _get_available_model(self) -> ModelConfig | None:
        """获取第一个可用的模型配置"""
        result = await self.db.execute(
            select(ModelConfig).where(
                ModelConfig.status == "normal",
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def _call_llm(
        self,
        model_config: ModelConfig,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """调用LLM API获取响应"""
        security = get_security_manager()
        api_key = security.decrypt_api_key(
            model_config.api_key_enc, model_config.api_key_iv
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_config.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 500,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{model_config.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"LLM API返回错误: {response.status_code} - {response.text}")

    async def import_skill_from_zip(self, zip_content: bytes) -> Skill:
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            skill_md_files = [name for name in zf.namelist() if os.path.basename(name.rstrip('/')) == "SKILL.md"]
            if not skill_md_files:
                raise ValueError("SKILL.md not found")
            skill_md_path = skill_md_files[0]

            base_dir = os.path.dirname(skill_md_path)
            if base_dir and not base_dir.endswith('/'):
                base_dir += '/'

            content = zf.read(skill_md_path).decode("utf-8")
            resource_files = []
            for name in zf.namelist():
                if name == skill_md_path or name.endswith('/'):
                    continue
                if base_dir and not name.startswith(base_dir):
                    continue
                resource_files.append(name)
            resource_infos = {name: zf.getinfo(name) for name in resource_files}
            resource_contents = {name: zf.read(name) for name in resource_files}

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("SKILL.md 格式错误：缺少 YAML frontmatter")

        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            logger.warning(f"SKILL.md YAML解析失败: {e}")
            raise ValueError("SKILL.md YAML 解析失败")

        if not isinstance(frontmatter, dict):
            raise ValueError("SKILL.md frontmatter 格式错误")

        name = frontmatter.get("name")
        description = frontmatter.get("description")

        if not name:
            raise ValueError("SKILL.md 缺少 name 字段")
        if not description:
            raise ValueError("SKILL.md 缺少 description 字段")

        name = name.lower()
        name = name.replace("_", "-")
        name = re.sub(r"[^a-z0-9-]", "", name)
        name = name.strip("-")[:64]
        if not name:
            name = "imported-skill"

        if not re.match(r"^[a-z0-9-]+$", name):
            raise ValueError("name 格式不正确，仅允许小写字母、数字和连字符")
        if len(name) > 64:
            raise ValueError("name 长度不能超过 64 个字符")
        if len(description) > 1024:
            raise ValueError("description 长度不能超过 1024 个字符")

        existing = await self.db.execute(
            select(Skill).where(Skill.name == name)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Skill name already exists")

        body = parts[2].strip()

        skill = Skill(
            name=name,
            display_name=name,
            description=description,
            skill_body=body,
            tags=[],
            category="general",
            is_builtin=False,
            version="1.0.0",
            status="active",
        )
        self.db.add(skill)
        await self.db.flush()

        # Create disk directory for skill resources (best-effort)
        skill_dir = os.path.join("uploads", "skills", str(skill.id))
        disk_writable = True
        try:
            os.makedirs(skill_dir, exist_ok=True)
        except OSError:
            logger.warning(f"无法创建资源目录（只读文件系统）: {skill_dir}")
            disk_writable = False

        for file_name, info in resource_infos.items():
            relative_name = file_name[len(base_dir):] if base_dir else file_name
            mime_type, _ = mimetypes.guess_type(file_name)
            file_path = None

            if disk_writable:
                file_path = f"uploads/skills/{skill.id}/{relative_name}"
                raw_bytes = resource_contents[file_name]
                full_path = os.path.join(skill_dir, relative_name)
                try:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "wb") as f:
                        f.write(raw_bytes)
                except OSError as e:
                    logger.warning(f"资源文件写入失败: {relative_name}, 错误: {e}")

            # Extract file content for DB persistence (text files only)
            file_content = None
            content_bytes = resource_contents[file_name]
            logger.debug(f"资源文件 content_bytes: name={relative_name}, raw_bytes_len={len(content_bytes)}, ext={os.path.splitext(file_name)[1].lower()}")
            text_extensions = {".py", ".md", ".yaml", ".yml", ".txt", ".json", ".css", ".html", ".js", ".ts", ".sh", ".bat", ".cfg", ".ini", ".toml", ".xml", ".svg", ".rst", ".sql", ".env"}
            ext = os.path.splitext(file_name)[1].lower()
            is_text = (
                (mime_type and (mime_type.startswith("text/") or mime_type in ("application/json", "application/javascript", "application/xml")))
                or ext in text_extensions
            )
            if is_text:
                try:
                    text = content_bytes.decode("utf-8", errors="replace")
                    logger.debug(f"资源文件解码: name={relative_name}, decoded_text_len={len(text)}, raw_bytes_len={len(content_bytes)}")
                    if len(content_bytes) <= 1048576:
                        file_content = text
                    else:
                        file_content = text[:5000] + f"\n\n[... 内容已截断，原文件大小: {len(content_bytes)} bytes]"
                        logger.warning(f"资源文件过大({len(content_bytes)} bytes)，仅存储前5000字符: {relative_name}")
                    if file_content is not None and len(file_content) != len(text):
                        logger.warning(f"资源文件内容长度异常: name={relative_name}, expected={len(text)}, actual={len(file_content)}")
                except Exception as e:
                    logger.warning(f"资源文件解码失败: {relative_name}, 错误: {e}")
            else:
                logger.debug(f"资源文件非文本: name={relative_name}, mime={mime_type}, ext={ext}")

            logger.debug(f"资源文件最终 file_content: name={relative_name}, content_len={len(file_content) if file_content else 0}")
            resource = SkillResource(
                skill_id=skill.id,
                file_name=relative_name,
                file_path=file_path,
                file_size=info.file_size,
                mime_type=mime_type,
                file_content=file_content,
            )
            self.db.add(resource)

        await self.db.commit()

        readback_result = await self.db.execute(
            select(SkillResource).where(SkillResource.skill_id == skill.id)
        )
        stored_resources = readback_result.scalars().all()
        for sr in stored_resources:
            db_len = len(sr.file_content) if sr.file_content else 0
            logger.debug(f"回读校验: name={sr.file_name}, db_content_len={db_len}")

        await self.db.refresh(skill)
        return skill

    async def export_skill_to_zip(self, skill_id: str) -> bytes:
        result = await self.db.execute(
            select(Skill)
            .options(selectinload(Skill.resources))
            .where(Skill.id == skill_id)
        )
        skill = result.scalar_one_or_none()

        if not skill:
            raise SkillNotFoundError()

        frontmatter = {
            "name": skill.name,
            "description": skill.description or "",
        }
        yaml_content = yaml.dump(
            frontmatter, allow_unicode=True, default_flow_style=False
        ).strip()
        skill_md = f"---\n{yaml_content}\n---\n{skill.skill_body or ''}\n"

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("SKILL.md", skill_md)

            for resource in skill.resources:
                if resource.file_path and os.path.isfile(resource.file_path):
                    zf.write(resource.file_path, resource.file_name)

        buf.seek(0)
        return buf.read()
