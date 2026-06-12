"""
Graph Query Service
图谱查询服务
"""

import logging
from typing import Any

from app.graph.neo4j_client import neo4j_manager

logger = logging.getLogger(__name__)


class GraphQueryService:

    async def get_agent_capability_chain(self, agent_id: str) -> list[dict[str, Any]]:
        if not neo4j_manager.enabled:
            return []
        try:
            records = await neo4j_manager.run(
                """
                MATCH (a:Agent {id: $agent_id})
                OPTIONAL MATCH (a)-[:HAS_SUB_AGENT]->(sub:Agent)
                OPTIONAL MATCH (sub)-[:HAS_KNOWLEDGE_DOC]->(doc:KnowledgeDocument)
                OPTIONAL MATCH (sub)-[:HAS_QA]->(qa:KnowledgeQA)
                OPTIONAL MATCH (sub)-[:HAS_SKILL]->(skill:Skill)
                OPTIONAL MATCH (sub)-[:HAS_TOOL]->(tool:Tool)
                RETURN a, sub, doc, qa, skill, tool
                """,
                agent_id=agent_id,
            )
            return records
        except Exception:
            logger.warning("get_agent_capability_chain failed", exc_info=True)
            return []

    async def find_related_knowledge(self, qa_id: str) -> list[dict[str, Any]]:
        if not neo4j_manager.enabled:
            return []
        try:
            records = await neo4j_manager.run(
                """
                MATCH (qa:KnowledgeQA {id: $qa_id})<-[:HAS_QA]-(agent:Agent)
                OPTIONAL MATCH (agent)-[:HAS_QA]->(other_qa:KnowledgeQA)
                WHERE other_qa.id <> $qa_id
                OPTIONAL MATCH (agent)-[:HAS_KNOWLEDGE_DOC]->(doc:KnowledgeDocument)
                RETURN agent, other_qa, doc
                """,
                qa_id=qa_id,
            )
            return records
        except Exception:
            logger.warning("find_related_knowledge failed", exc_info=True)
            return []

    async def get_agent_hierarchy(self, root_agent_id: str) -> list[dict[str, Any]]:
        if not neo4j_manager.enabled:
            return []
        try:
            records = await neo4j_manager.run(
                """
                MATCH path = (root:Agent {id: $root_id})-[:HAS_SUB_AGENT*0..3]->(agent:Agent)
                RETURN agent, length(path) as depth
                ORDER BY depth
                """,
                root_id=root_agent_id,
            )
            return records
        except Exception:
            logger.warning("get_agent_hierarchy failed", exc_info=True)
            return []

    async def search_agents_by_capability(self, keyword: str) -> list[dict[str, Any]]:
        if not neo4j_manager.enabled:
            return []
        try:
            records = await neo4j_manager.run(
                """
                MATCH (a:Agent)
                WHERE a.name CONTAINS $keyword OR a.type CONTAINS $keyword
                OPTIONAL MATCH (a)-[:HAS_SKILL]->(s:Skill)
                OPTIONAL MATCH (a)-[:HAS_TOOL]->(t:Tool)
                RETURN a, collect(DISTINCT s.name) as skills, collect(DISTINCT t.name) as tools
                """,
                keyword=keyword,
            )
            return records
        except Exception:
            logger.warning("search_agents_by_capability failed", exc_info=True)
            return []

    async def get_user_interaction_history(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        if not neo4j_manager.enabled:
            return []
        try:
            records = await neo4j_manager.run(
                """
                MATCH (u:User {id: $user_id})-[:INITIATED]->(c:Conversation)-[:HANDLED_BY]->(a:Agent)
                OPTIONAL MATCH (a)-[:HAS_SKILL]->(s:Skill)
                OPTIONAL MATCH (a)-[:HAS_TOOL]->(t:Tool)
                RETURN c, a, collect(DISTINCT s.name) as skills, collect(DISTINCT t.name) as tools
                ORDER BY c.created_at DESC
                LIMIT $limit
                """,
                user_id=user_id, limit=limit,
            )
            return records
        except Exception:
            logger.warning("get_user_interaction_history failed", exc_info=True)
            return []


graph_query_service = GraphQueryService()