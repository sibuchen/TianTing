"""
Neo4j Graph Database Client
Neo4j图数据库客户端
"""

import logging

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jManager:

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None
        self._enabled = settings.neo4j_enabled

    @property
    def enabled(self) -> bool:
        return self._enabled and self._driver is not None

    async def init(self) -> None:
        if not self._enabled:
            logger.info("Neo4j is disabled, skipping initialization")
            return
        try:
            self._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            await self._driver.verify_connectivity()
            await self._ensure_constraints()
            logger.info("Neo4j initialized successfully at %s", settings.neo4j_uri)
        except Exception:
            logger.warning("Failed to initialize Neo4j, disabling", exc_info=True)
            self._enabled = False
            if self._driver:
                await self._driver.close()
            self._driver = None

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def _ensure_constraints(self) -> None:
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:KnowledgeDocument) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (q:KnowledgeQA) REQUIRE q.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tool) REQUIRE t.id IS UNIQUE",
        ]
        async with self._driver.session() as session:
            for cypher in constraints:
                try:
                    await session.run(cypher)
                except Exception:
                    logger.warning("Failed to create constraint: %s", cypher[:50])

    async def run(self, cypher: str, **params) -> list[dict]:
        if not self.enabled:
            return []
        try:
            async with self._driver.session() as session:
                result = await session.run(cypher, **params)
                records = await result.data()
                return records
        except Exception:
            logger.warning("Neo4j query failed", exc_info=True)
            return []

    async def merge_agent(self, agent_id: str, name: str, agent_type: str, is_enabled: bool) -> bool:
        if not self.enabled:
            return False
        try:
            await self.run(
                """
                MERGE (a:Agent {id: $id})
                SET a.name = $name, a.type = $type, a.is_enabled = $is_enabled
                """,
                id=agent_id, name=name, type=agent_type, is_enabled=is_enabled,
            )
            return True
        except Exception:
            logger.warning("Neo4j merge_agent failed", exc_info=True)
            return False

    async def merge_relationship(
        self,
        from_id: str,
        to_id: str,
        from_label: str,
        to_label: str,
        rel_type: str,
    ) -> bool:
        if not self.enabled:
            return False
        try:
            cypher = f"""
                MATCH (a:{from_label} {{id: $from_id}})
                MATCH (b:{to_label} {{id: $to_id}})
                MERGE (a)-[r:{rel_type}]->(b)
            """
            await self.run(cypher, from_id=from_id, to_id=to_id)
            return True
        except Exception:
            logger.warning("Neo4j merge_relationship failed", exc_info=True)
            return False

    async def delete_node(self, node_id: str, label: str) -> bool:
        if not self.enabled:
            return False
        try:
            await self.run(
                f"MATCH (n:{label} {{id: $id}}) DETACH DELETE n",
                id=node_id,
            )
            return True
        except Exception:
            logger.warning("Neo4j delete_node failed", exc_info=True)
            return False

    async def clear_all(self) -> bool:
        if not self.enabled:
            return False
        try:
            await self.run("MATCH (n) DETACH DELETE n")
            return True
        except Exception:
            logger.warning("Neo4j clear_all failed", exc_info=True)
            return False

    async def merge_user(self, user_id: str, name: str) -> bool:
        if not self.enabled:
            return False
        try:
            await self.run(
                "MERGE (u:User {id: $id}) SET u.name = $name",
                id=user_id, name=name,
            )
            return True
        except Exception:
            logger.warning("Neo4j merge_user failed", exc_info=True)
            return False

    async def merge_conversation(self, conversation_id: str, intent: str = "", channel: str = "") -> bool:
        if not self.enabled:
            return False
        try:
            await self.run(
                "MERGE (c:Conversation {id: $id}) SET c.intent = $intent, c.channel = $channel",
                id=conversation_id, intent=intent, channel=channel,
            )
            return True
        except Exception:
            logger.warning("Neo4j merge_conversation failed", exc_info=True)
            return False


neo4j_manager = Neo4jManager()