// ============================================================================
// TianTing Neo4j Constraints & Indexes
// 天听系统 Neo4j 图数据库约束和索引
// ============================================================================

CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT conversation_id_unique IF NOT EXISTS FOR (c:Conversation) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT doc_id_unique IF NOT EXISTS FOR (d:KnowledgeDocument) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT qa_id_unique IF NOT EXISTS FOR (q:KnowledgeQA) REQUIRE q.id IS UNIQUE;

CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT tool_id_unique IF NOT EXISTS FOR (t:Tool) REQUIRE t.id IS UNIQUE;

CREATE INDEX agent_name_idx IF NOT EXISTS FOR (a:Agent) ON (a.name);

CREATE INDEX user_name_idx IF NOT EXISTS FOR (u:User) ON (u.name);