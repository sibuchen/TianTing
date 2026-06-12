"""
Graph Sync Service
图谱同步服务：从 PostgreSQL 关系表同步到 Neo4j
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.neo4j_client import neo4j_manager

logger = logging.getLogger(__name__)


class GraphSyncService:

    async def full_sync(self, db: AsyncSession) -> dict:
        if not neo4j_manager.enabled:
            return {"status": "disabled"}

        try:
            await neo4j_manager.clear_all()

            from app.models.agent import Agent
            from app.models.agent import AgentSubAgent, AgentKnowledgeDocument, AgentKnowledgeQA
            from app.models.agent import AgentSkill, AgentTool
            from app.models.knowledge import KnowledgeDocument, KnowledgeQA
            from app.models.skill import Skill
            from app.models.tool import ToolConfig

            result = await db.execute(select(Agent))
            agents = result.scalars().all()
            for agent in agents:
                await neo4j_manager.merge_agent(
                    str(agent.id), agent.name, agent.type, agent.is_enabled
                )

            result = await db.execute(select(AgentSubAgent))
            for rel in result.scalars().all():
                await neo4j_manager.merge_relationship(
                    str(rel.parent_agent_id), str(rel.sub_agent_id),
                    "Agent", "Agent", "HAS_SUB_AGENT",
                )

            result = await db.execute(select(AgentKnowledgeDocument))
            for rel in result.scalars().all():
                await neo4j_manager.merge_relationship(
                    str(rel.agent_id), str(rel.document_id),
                    "Agent", "KnowledgeDocument", "HAS_KNOWLEDGE_DOC",
                )

            result = await db.execute(select(AgentKnowledgeQA))
            for rel in result.scalars().all():
                await neo4j_manager.merge_relationship(
                    str(rel.agent_id), str(rel.qa_id),
                    "Agent", "KnowledgeQA", "HAS_QA",
                )

            result = await db.execute(select(AgentSkill))
            for rel in result.scalars().all():
                await neo4j_manager.merge_relationship(
                    str(rel.agent_id), str(rel.skill_id),
                    "Agent", "Skill", "HAS_SKILL",
                )

            result = await db.execute(select(AgentTool))
            for rel in result.scalars().all():
                await neo4j_manager.merge_relationship(
                    str(rel.agent_id), str(rel.tool_config_id),
                    "Agent", "Tool", "HAS_TOOL",
                )

            logger.info("Graph full sync completed")
            return {"status": "success", "agents": len(agents)}
        except Exception:
            logger.warning("Graph full sync failed", exc_info=True)
            return {"status": "error"}

    async def sync_agent(self, agent_id: str, name: str, agent_type: str, is_enabled: bool) -> None:
        await neo4j_manager.merge_agent(agent_id, name, agent_type, is_enabled)

    async def sync_sub_agent_relation(self, parent_id: str, sub_id: str) -> None:
        await neo4j_manager.merge_relationship(parent_id, sub_id, "Agent", "Agent", "HAS_SUB_AGENT")

    async def sync_knowledge_doc_relation(self, agent_id: str, doc_id: str) -> None:
        await neo4j_manager.merge_relationship(agent_id, doc_id, "Agent", "KnowledgeDocument", "HAS_KNOWLEDGE_DOC")

    async def sync_qa_relation(self, agent_id: str, qa_id: str) -> None:
        await neo4j_manager.merge_relationship(agent_id, qa_id, "Agent", "KnowledgeQA", "HAS_QA")

    async def remove_sub_agent_relation(self, parent_id: str, sub_id: str) -> None:
        if not neo4j_manager.enabled:
            return
        await neo4j_manager.run(
            "MATCH (a:Agent {id: $parent_id})-[r:HAS_SUB_AGENT]->(b:Agent {id: $sub_id}) DELETE r",
            parent_id=parent_id, sub_id=sub_id,
        )

    async def remove_knowledge_doc_relation(self, agent_id: str, doc_id: str) -> None:
        if not neo4j_manager.enabled:
            return
        await neo4j_manager.run(
            "MATCH (a:Agent {id: $agent_id})-[r:HAS_KNOWLEDGE_DOC]->(d:KnowledgeDocument {id: $doc_id}) DELETE r",
            agent_id=agent_id, doc_id=doc_id,
        )

    async def remove_qa_relation(self, agent_id: str, qa_id: str) -> None:
        if not neo4j_manager.enabled:
            return
        await neo4j_manager.run(
            "MATCH (a:Agent {id: $agent_id})-[r:HAS_QA]->(q:KnowledgeQA {id: $qa_id}) DELETE r",
            agent_id=agent_id, qa_id=qa_id,
        )

    async def sync_user(self, user_id: str, name: str) -> None:
        await neo4j_manager.merge_user(user_id, name)

    async def sync_conversation_relation(
        self, user_id: str, conversation_id: str, agent_id: str, intent: str = "", channel: str = ""
    ) -> None:
        if not neo4j_manager.enabled:
            return
        await neo4j_manager.merge_user(user_id, "")
        await neo4j_manager.merge_conversation(conversation_id, intent, channel)
        await neo4j_manager.merge_relationship(user_id, conversation_id, "User", "Conversation", "INITIATED")
        await neo4j_manager.merge_relationship(conversation_id, agent_id, "Conversation", "Agent", "HANDLED_BY")


graph_sync_service = GraphSyncService()