"""
Agent Service
Agent服务：CRUD/状态管理
"""

import logging

from sqlalchemy import select, update, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.graph.sync_service import graph_sync_service
from app.core.exceptions import (
    AgentNotFoundError,
    AgentNameExistsError,
    CannotDisableOrchestratorError,
    InvalidAgentTypeError,
    SkillAlreadyAssignedError,
    MCPServerNotFoundError,
    ToolNotFoundError,
)
from app.models.agent import Agent, AgentSkill, AgentMCPServer, AgentTool, AgentSubAgent, AgentKnowledgeDocument, AgentKnowledgeQA
from app.models.skill import Skill
from app.models.mcp_server import MCPServer
from app.models.tool import ToolConfig
from app.models.conversation import Conversation
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentDetail,
    AgentListItem,
    AgentStats,
    ModelInfo,
    SkillInfo,
    MCPServerInfo,
    ToolInfo,
    SubAgentInfo,
    KnowledgeDocInfo,
    KnowledgeQAInfo,
)

logger = logging.getLogger(__name__)


class AgentService:
    """Agent服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_agents(self) -> list[AgentListItem]:
        """获取Agent列表"""
        result = await self.db.execute(
            select(Agent)
            .options(
                selectinload(Agent.model_config),
                selectinload(Agent.skills),
                selectinload(Agent.tools),
            )
            .order_by(Agent.created_at.desc())
        )
        agents = result.scalars().all()

        return [
            AgentListItem(
                id=agent.id,
                name=agent.name,
                type=agent.type,
                description=agent.description,
                icon=agent.icon,
                icon_color=agent.icon_color,
                is_enabled=agent.is_enabled,
                model_name=agent.model_config.name if agent.model_config else None,
                skills_count=len(agent.skills),
                tools_count=len(agent.tools),
            )
            for agent in agents
        ]

    async def create_agent(self, data: AgentCreate) -> Agent:
        """创建Agent"""
        result = await self.db.execute(
            select(Agent).where(Agent.name == data.name)
        )
        if result.scalar_one_or_none():
            raise AgentNameExistsError()

        agent = Agent(
            name=data.name,
            type=data.type,
            description=data.description,
            is_enabled=False,
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)

        try:
            await graph_sync_service.sync_agent(str(agent.id), agent.name, agent.type, agent.is_enabled)
        except Exception:
            pass

        return agent

    async def get_agent_detail(self, agent_id: str) -> AgentDetail:
        """获取Agent详情"""
        result = await self.db.execute(
            select(Agent)
            .options(
                selectinload(Agent.model_config),
                selectinload(Agent.skills).selectinload(AgentSkill.skill),
                selectinload(Agent.mcp_servers).selectinload(AgentMCPServer.mcp_server),
                selectinload(Agent.tools).selectinload(AgentTool.tool_config),
                selectinload(Agent.sub_agents).selectinload(AgentSubAgent.sub_agent),
                selectinload(Agent.knowledge_documents).selectinload(AgentKnowledgeDocument.document),
                selectinload(Agent.knowledge_qa_list).selectinload(AgentKnowledgeQA.qa),
            )
            .where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            raise AgentNotFoundError()

        conv_result = await self.db.execute(
            select(func.count(Conversation.id))
        )
        total_conversations = conv_result.scalar() or 0

        resolved_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.status == "resolved",
            )
        )
        resolved_conversations = resolved_result.scalar() or 0

        resolution_rate = (
            (resolved_conversations / total_conversations * 100)
            if total_conversations > 0
            else 0.0
        )

        return AgentDetail(
            id=agent.id,
            name=agent.name,
            type=agent.type,
            description=agent.description,
            system_prompt=agent.system_prompt,
            is_enabled=agent.is_enabled,
            model_info=ModelInfo(
                id=agent.model_config.id,
                name=agent.model_config.name,
                provider=agent.model_config.base_url,
            )
            if agent.model_config
            else None,
            skills=[
                SkillInfo(
                    id=as_.skill.id,
                    name=as_.skill.name,
                    name_en=None,
                    icon=as_.skill.icon,
                )
                for as_ in agent.skills
                if as_.skill is not None
            ],
            mcp_servers=[
                MCPServerInfo(
                    id=ams.mcp_server.id,
                    name=ams.mcp_server.name,
                    status=ams.mcp_server.status,
                )
                for ams in agent.mcp_servers
                if ams.mcp_server is not None
            ],
            tools=[
                ToolInfo(
                    id=at.tool_config.id,
                    name=at.tool_config.name,
                    is_enabled=at.is_enabled,
                )
                for at in agent.tools
                if at.tool_config is not None
            ],
            stats=AgentStats(
                total_conversations=total_conversations,
                resolution_rate=round(resolution_rate, 1),
            ),
            transfer_keywords=agent.transfer_keywords,
            human_agent_id=agent.human_agent_id,
            supported_channels=agent.supported_channels,
            sub_agents=[
                SubAgentInfo(
                    id=asa.sub_agent.id,
                    name=asa.sub_agent.name,
                    type=asa.sub_agent.type,
                    description=asa.sub_agent.description,
                    is_enabled=asa.sub_agent.is_enabled,
                )
                for asa in agent.sub_agents
                if asa.sub_agent is not None
            ],
            knowledge_documents=[
                KnowledgeDocInfo(
                    id=akd.document.id,
                    file_name=akd.document.file_name,
                    vector_status=akd.document.vector_status,
                )
                for akd in agent.knowledge_documents
                if akd.document is not None
            ],
            knowledge_qa_list=[
                KnowledgeQAInfo(
                    id=akq.qa.id,
                    question=akq.qa.question,
                )
                for akq in agent.knowledge_qa_list
                if akq.qa is not None
            ],
        )

    async def update_agent(self, agent_id: str, data: AgentUpdate) -> None:
        """更新Agent"""
        agent = await self._get_agent_or_raise(agent_id)

        if data.name and data.name != agent.name:
            result = await self.db.execute(
                select(Agent).where(Agent.name == data.name)
            )
            if result.scalar_one_or_none():
                raise AgentNameExistsError()

        # 使用 ORM 对象属性直接赋值，避免字段名过滤出现遗漏
        # 允许更新的字段白名单（对应 Agent 模型的列属性名）
        UPDATABLE_FIELDS = {
            "name", "type", "description", "system_prompt", "is_enabled",
            "transfer_keywords", "human_agent_id", "supported_channels",
            "icon", "icon_color",
        }
        raw_data = data.model_dump(exclude_unset=True, by_alias=False)

        changed = False
        for field, value in raw_data.items():
            if field in UPDATABLE_FIELDS:
                setattr(agent, field, value)
                changed = True

        if data.model_config_id is not None:
            agent.model_config_id = data.model_config_id
            changed = True
            logger.info("update_agent agent_id=%s model_config_id=%s (explicit set)", agent_id, data.model_config_id)
        elif data.model_fields_set and "model_config_id" in data.model_fields_set:
            agent.model_config_id = None
            changed = True
            logger.info("update_agent agent_id=%s model_config_id=None (explicit clear)", agent_id)

        if changed:
            await self.db.commit()
            await self.db.refresh(agent)

        try:
            await graph_sync_service.sync_agent(str(agent.id), agent.name, agent.type, agent.is_enabled)
        except Exception:
            pass

        logger.debug("update_agent agent_id=%s raw_data=%s changed=%s model_config_id=%s", agent_id, raw_data, changed, agent.model_config_id)

    async def toggle_agent(self, agent_id: str, is_enabled: bool) -> None:
        """切换Agent启用/禁用"""
        agent = await self._get_agent_or_raise(agent_id)

        if not is_enabled and agent.type == "orchestrator":
            orchestrator_count = await self.db.execute(
                select(func.count(Agent.id)).where(
                    and_(
                        Agent.type == "orchestrator",
                        Agent.is_enabled == True,
                    )
                )
            )
            if orchestrator_count.scalar() <= 1:
                raise CannotDisableOrchestratorError()

        await self.db.execute(
            update(Agent)
            .where(Agent.id == agent_id)
            .values(is_enabled=is_enabled)
        )
        await self.db.commit()

        try:
            await graph_sync_service.sync_agent(str(agent.id), agent.name, agent.type, is_enabled)
        except Exception:
            pass

    async def assign_skill(self, agent_id: str, skill_id: str) -> None:
        """分配Skill"""
        await self._get_agent_or_raise(agent_id)

        skill_result = await self.db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        if not skill_result.scalar_one_or_none():
            raise ToolNotFoundError()

        result = await self.db.execute(
            select(AgentSkill).where(
                and_(
                    AgentSkill.agent_id == agent_id,
                    AgentSkill.skill_id == skill_id,
                )
            )
        )
        if result.scalar_one_or_none():
            raise SkillAlreadyAssignedError()

        agent_skill = AgentSkill(agent_id=agent_id, skill_id=skill_id)
        self.db.add(agent_skill)
        await self.db.commit()

    async def remove_skill(self, agent_id: str, skill_id: str) -> None:
        """移除Skill"""
        await self._get_agent_or_raise(agent_id)

        await self.db.execute(
            delete(AgentSkill).where(
                and_(
                    AgentSkill.agent_id == agent_id,
                    AgentSkill.skill_id == skill_id,
                )
            )
        )
        await self.db.commit()

    async def link_mcp_server(
        self, agent_id: str, mcp_server_id: str, is_linked: bool
    ) -> None:
        """连接/断开MCP Server"""
        await self._get_agent_or_raise(agent_id)

        mcp_result = await self.db.execute(
            select(MCPServer).where(MCPServer.id == mcp_server_id)
        )
        if not mcp_result.scalar_one_or_none():
            raise MCPServerNotFoundError()

        result = await self.db.execute(
            select(AgentMCPServer).where(
                and_(
                    AgentMCPServer.agent_id == agent_id,
                    AgentMCPServer.mcp_server_id == mcp_server_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            await self.db.execute(
                update(AgentMCPServer)
                .where(AgentMCPServer.id == existing.id)
                .values(is_linked=is_linked)
            )
        else:
            agent_mcp = AgentMCPServer(
                agent_id=agent_id,
                mcp_server_id=mcp_server_id,
                is_linked=is_linked,
            )
            self.db.add(agent_mcp)

        await self.db.commit()

    async def unlink_mcp_server(self, agent_id: str, mcp_server_id: str) -> None:
        """断开MCP Server"""
        await self._get_agent_or_raise(agent_id)

        await self.db.execute(
            delete(AgentMCPServer).where(
                and_(
                    AgentMCPServer.agent_id == agent_id,
                    AgentMCPServer.mcp_server_id == mcp_server_id,
                )
            )
        )
        await self.db.commit()

    async def toggle_tool(self, agent_id: str, tool_id: str, is_enabled: bool) -> None:
        """启用/禁用Agent工具（禁用时删除关联，启用时创建关联）"""
        await self._get_agent_or_raise(agent_id)

        tool_result = await self.db.execute(
            select(ToolConfig).where(ToolConfig.id == tool_id)
        )
        if not tool_result.scalar_one_or_none():
            raise ToolNotFoundError()

        result = await self.db.execute(
            select(AgentTool).where(
                and_(
                    AgentTool.agent_id == agent_id,
                    AgentTool.tool_config_id == tool_id,
                )
            )
        )
        agent_tool = result.scalar_one_or_none()

        if is_enabled:
            if not agent_tool:
                new_agent_tool = AgentTool(
                    agent_id=agent_id,
                    tool_config_id=tool_id,
                    is_enabled=True,
                )
                self.db.add(new_agent_tool)
        else:
            if agent_tool:
                await self.db.execute(
                    delete(AgentTool).where(AgentTool.id == agent_tool.id)
                )

        await self.db.commit()

    async def _get_agent_or_raise(self, agent_id: str) -> Agent:
        """获取Agent或抛出异常"""
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise AgentNotFoundError()
        return agent

    async def delete_agent(self, agent_id: str) -> None:
        """删除Agent"""
        agent = await self._get_agent_or_raise(agent_id)
        await self.db.execute(
            delete(Agent).where(Agent.id == agent_id)
        )
        await self.db.commit()

    async def add_sub_agent(self, agent_id: str, sub_agent_id: str) -> None:
        await self._get_agent_or_raise(agent_id)
        result = await self.db.execute(select(Agent).where(Agent.id == sub_agent_id))
        if not result.scalar_one_or_none():
            raise AgentNotFoundError()
        existing = await self.db.execute(
            select(AgentSubAgent).where(
                and_(AgentSubAgent.parent_agent_id == agent_id, AgentSubAgent.sub_agent_id == sub_agent_id)
            )
        )
        if existing.scalar_one_or_none():
            return
        link = AgentSubAgent(parent_agent_id=agent_id, sub_agent_id=sub_agent_id)
        self.db.add(link)
        await self.db.commit()

        try:
            await graph_sync_service.sync_sub_agent_relation(agent_id, sub_agent_id)
        except Exception:
            pass

    async def remove_sub_agent(self, agent_id: str, sub_agent_id: str) -> None:
        await self._get_agent_or_raise(agent_id)
        await self.db.execute(
            delete(AgentSubAgent).where(
                and_(AgentSubAgent.parent_agent_id == agent_id, AgentSubAgent.sub_agent_id == sub_agent_id)
            )
        )
        await self.db.commit()

        try:
            await graph_sync_service.remove_sub_agent_relation(agent_id, sub_agent_id)
        except Exception:
            pass

    async def add_knowledge_document(self, agent_id: str, document_id: str) -> None:
        await self._get_agent_or_raise(agent_id)
        existing = await self.db.execute(
            select(AgentKnowledgeDocument).where(
                and_(AgentKnowledgeDocument.agent_id == agent_id, AgentKnowledgeDocument.document_id == document_id)
            )
        )
        if existing.scalar_one_or_none():
            return
        link = AgentKnowledgeDocument(agent_id=agent_id, document_id=document_id)
        self.db.add(link)
        await self.db.commit()

        try:
            await graph_sync_service.sync_knowledge_doc_relation(agent_id, document_id)
        except Exception:
            pass

    async def remove_knowledge_document(self, agent_id: str, document_id: str) -> None:
        await self._get_agent_or_raise(agent_id)
        await self.db.execute(
            delete(AgentKnowledgeDocument).where(
                and_(AgentKnowledgeDocument.agent_id == agent_id, AgentKnowledgeDocument.document_id == document_id)
            )
        )
        await self.db.commit()

        try:
            await graph_sync_service.remove_knowledge_doc_relation(agent_id, document_id)
        except Exception:
            pass

    async def add_knowledge_qa(self, agent_id: str, qa_id: str) -> None:
        await self._get_agent_or_raise(agent_id)
        existing = await self.db.execute(
            select(AgentKnowledgeQA).where(
                and_(AgentKnowledgeQA.agent_id == agent_id, AgentKnowledgeQA.qa_id == qa_id)
            )
        )
        if existing.scalar_one_or_none():
            return
        link = AgentKnowledgeQA(agent_id=agent_id, qa_id=qa_id)
        self.db.add(link)
        await self.db.commit()

        try:
            await graph_sync_service.sync_qa_relation(agent_id, qa_id)
        except Exception:
            pass

    async def remove_knowledge_qa(self, agent_id: str, qa_id: str) -> None:
        await self._get_agent_or_raise(agent_id)
        await self.db.execute(
            delete(AgentKnowledgeQA).where(
                and_(AgentKnowledgeQA.agent_id == agent_id, AgentKnowledgeQA.qa_id == qa_id)
            )
        )
        await self.db.commit()

        try:
            await graph_sync_service.remove_qa_relation(agent_id, qa_id)
        except Exception:
            pass
