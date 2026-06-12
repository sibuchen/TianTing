-- ============================================================================
-- 天听（TianTing）数据库初始化脚本
-- ============================================================================
-- 多数据库架构说明
-- ============================================================================
-- 本文件仅管理 PostgreSQL 业务数据库的表结构。
-- 完整的数据存储架构包含以下数据库，各有专属初始化脚本：
--
--   数据库        用途                      初始化脚本
--   ───────────  ────────────────────────  ──────────────────────────
--   PostgreSQL   业务数据（用户/Agent/对话）  database/init.sql + seed.sql
--   Redis DB 0   缓存/限流/Pub-Sub          无需初始化脚本
--   Redis DB 1   ARQ 任务队列               无需初始化脚本
--   Qdrant       向量检索（文档块/QA）       自动创建 Collection
--   Neo4j        知识图谱（Agent关系）       database/neo4j/01_constraints.cypher
--   MongoDB      日志/事件/转录              database/mongodb/01_init.js
--   Snowflake    数据仓库/BI分析             database/snowflake/*.sql（云服务，需单独部署）
--
-- ============================================================================
-- 版本：v1.4
-- 日期：2026-05-16
-- 数据库：PostgreSQL 16+ with pgvector
-- 说明：本脚本可直接在 PostgreSQL 中执行，完成数据库和表的初始化
-- ============================================================================

-- ============================================================================
-- Part 1: 创建数据库
-- ============================================================================
-- 注意：以下语句需要以超级用户身份执行
-- 如果数据库已存在，可跳过此部分

-- CREATE DATABASE tianting
--     WITH ENCODING = 'UTF8'
--     LC_COLLATE = 'en_US.UTF-8'
--     LC_CTYPE = 'en_US.UTF-8'
--     TEMPLATE = template0;

-- 连接到目标数据库后执行以下内容
-- \c tianting

-- ============================================================================
-- Part 2: 启用扩展
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";       -- UUID 生成
CREATE EXTENSION IF NOT EXISTS "vector";          -- pgvector 向量支持
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- 模糊搜索（Q&A 检索）

-- ============================================================================
-- Part 3: 创建通用函数和类型
-- ============================================================================

-- 3.1 updated_at 自动更新触发器函数
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Part 4: 建表语句（按依赖顺序）
-- ============================================================================

-- --------------------------------------------------------------------------
-- 4.1 users — 管理后台用户表
-- --------------------------------------------------------------------------
CREATE TABLE users (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50)     NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    phone           VARCHAR(20),
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(20)     NOT NULL DEFAULT 'operator',
    avatar          VARCHAR(500),
    status          VARCHAR(20)     NOT NULL DEFAULT 'active',
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_email    UNIQUE (email),
    CONSTRAINT ck_users_role     CHECK (role IN ('admin', 'operator')),
    CONSTRAINT ck_users_status   CHECK (status IN ('active', 'disabled')),
    CONSTRAINT uk_users_phone   UNIQUE (phone)
);

COMMENT ON TABLE  users IS '管理后台用户表';
COMMENT ON COLUMN users.id IS '用户 ID';
COMMENT ON COLUMN users.username IS '用户名';
COMMENT ON COLUMN users.email IS '邮箱地址';
COMMENT ON COLUMN users.password_hash IS 'bcrypt 哈希后的密码';
COMMENT ON COLUMN users.role IS '角色：admin / operator';
COMMENT ON COLUMN users.avatar IS '头像 URL';
COMMENT ON COLUMN users.status IS '状态：active / disabled';
COMMENT ON COLUMN users.phone IS '手机号码';
COMMENT ON COLUMN users.last_login_at IS '最后登录时间';

-- --------------------------------------------------------------------------
-- 4.2 refresh_tokens — 刷新令牌表
-- --------------------------------------------------------------------------
CREATE TABLE refresh_tokens (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID            NOT NULL REFERENCES users(id),
    token_hash      VARCHAR(255)    NOT NULL,
    expires_at      TIMESTAMPTZ     NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_refresh_tokens_token_hash UNIQUE (token_hash)
);

COMMENT ON TABLE  refresh_tokens IS 'JWT 刷新令牌表';
COMMENT ON COLUMN refresh_tokens.user_id IS '所属用户';
COMMENT ON COLUMN refresh_tokens.token_hash IS '令牌哈希值';
COMMENT ON COLUMN refresh_tokens.expires_at IS '过期时间';

-- --------------------------------------------------------------------------
-- 4.3 model_configs — 模型 API 配置表
-- --------------------------------------------------------------------------
CREATE TABLE model_configs (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100)    NOT NULL,
    base_url        VARCHAR(500)    NOT NULL,
    api_key_enc     TEXT            NOT NULL,
    api_key_iv      VARCHAR(32)     NOT NULL,
    model_id        VARCHAR(100)    NOT NULL,
    capabilities    JSONB,
    context_window  INTEGER,
    status          VARCHAR(20)     NOT NULL DEFAULT 'normal',
    last_tested_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_model_configs_status CHECK (status IN ('normal', 'error'))
);

COMMENT ON TABLE  model_configs IS '模型 API 配置表';
COMMENT ON COLUMN model_configs.name IS '显示名称，如 GPT-4o';
COMMENT ON COLUMN model_configs.base_url IS '模型 API 地址';
COMMENT ON COLUMN model_configs.api_key_enc IS 'AES-256-GCM 加密后的 API Key 密文';
COMMENT ON COLUMN model_configs.api_key_iv IS 'AES 加密初始化向量';
COMMENT ON COLUMN model_configs.model_id IS '模型标识，如 gpt-4o';
COMMENT ON COLUMN model_configs.capabilities IS '模型能力标记，如 ["chat_completion", "function_calling"]';
COMMENT ON COLUMN model_configs.context_window IS '上下文窗口大小';
COMMENT ON COLUMN model_configs.status IS '状态：normal / error';
COMMENT ON COLUMN model_configs.last_tested_at IS '最后测试连接时间';

-- --------------------------------------------------------------------------
-- 4.4 agents — Agent 配置表
-- --------------------------------------------------------------------------
CREATE TABLE agents (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(50)     NOT NULL,
    type            VARCHAR(20)     NOT NULL,
    description     VARCHAR(500),
    system_prompt   TEXT,
    is_enabled      BOOLEAN         NOT NULL DEFAULT false,
    icon            VARCHAR(50),
    icon_color      VARCHAR(10),
    model_config_id UUID            REFERENCES model_configs(id),
    transfer_keywords JSONB,
    human_agent_id UUID            REFERENCES users(id),
    supported_channels JSONB,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_agents_type CHECK (type IN ('orchestrator', 'faq', 'after-sale', 'custom'))
);

COMMENT ON TABLE  agents IS 'Agent 配置表';
COMMENT ON COLUMN agents.name IS 'Agent 名称';
COMMENT ON COLUMN agents.type IS '类型：orchestrator / faq / after-sale / custom';
COMMENT ON COLUMN agents.description IS '描述';
COMMENT ON COLUMN agents.system_prompt IS '系统提示词';
COMMENT ON COLUMN agents.is_enabled IS '是否启用';
COMMENT ON COLUMN agents.icon IS '图标标识';
COMMENT ON COLUMN agents.icon_color IS '图标颜色';
COMMENT ON COLUMN agents.model_config_id IS '绑定的模型配置';

-- --------------------------------------------------------------------------
-- 4.5 skills — 技能配置表
-- --------------------------------------------------------------------------
CREATE TABLE skills (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(100)    NOT NULL,
    display_name        VARCHAR(200),
    icon                VARCHAR(50),
    icon_color          VARCHAR(10),
    category            VARCHAR(50)     NOT NULL,
    description         TEXT,
    status              VARCHAR(20)     NOT NULL DEFAULT 'active',
    skill_body          TEXT,
    tags                JSONB,
    version             VARCHAR(20),
    author              VARCHAR(100),
    prompts             TEXT,
    is_builtin          BOOLEAN         NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_skills_status CHECK (status IN ('active', 'inactive'))
);

COMMENT ON TABLE  skills IS '技能配置表';
COMMENT ON COLUMN skills.name IS 'Anthropic规范名称（小写+连字符，max 64）';
COMMENT ON COLUMN skills.display_name IS '技能展示名称';
COMMENT ON COLUMN skills.category IS '分类';
COMMENT ON COLUMN skills.status IS '状态：active / inactive';
COMMENT ON COLUMN skills.skill_body IS '技能内容（提示词/脚本）';
COMMENT ON COLUMN skills.tags IS '标签列表 JSONB，如 ["sales"]';
COMMENT ON COLUMN skills.version IS '版本号';
COMMENT ON COLUMN skills.author IS '作者';
COMMENT ON COLUMN skills.prompts IS '提示词模板（兼容旧版）';
COMMENT ON COLUMN skills.is_builtin IS '是否内置';

-- --------------------------------------------------------------------------
-- 4.6 mcp_servers — MCP Server 配置表
-- --------------------------------------------------------------------------
CREATE TABLE mcp_servers (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100)    NOT NULL,
    transport_type  VARCHAR(20)     NOT NULL DEFAULT 'sse',
    url             VARCHAR(500),
    command         VARCHAR(500),
    args            JSONB,
    env             JSONB,
    status          VARCHAR(20)     NOT NULL DEFAULT 'offline',
    is_enabled      BOOLEAN         NOT NULL DEFAULT true,
    tools           JSONB,
    version         VARCHAR(50),
    last_tested_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_mcp_servers_transport_type CHECK (transport_type IN ('sse', 'stdio')),
    CONSTRAINT ck_mcp_servers_status CHECK (status IN ('online', 'offline'))
);

COMMENT ON TABLE  mcp_servers IS 'MCP Server 配置表';
COMMENT ON COLUMN mcp_servers.name IS 'Server 名称';
COMMENT ON COLUMN mcp_servers.transport_type IS '传输类型：sse / stdio';
COMMENT ON COLUMN mcp_servers.url IS 'Server 地址（SSE模式）';
COMMENT ON COLUMN mcp_servers.command IS '启动命令（stdio模式）';
COMMENT ON COLUMN mcp_servers.args IS '命令参数列表（stdio模式）';
COMMENT ON COLUMN mcp_servers.env IS '环境变量（stdio模式）';
COMMENT ON COLUMN mcp_servers.status IS '状态：online / offline';
COMMENT ON COLUMN mcp_servers.is_enabled IS '是否启用';
COMMENT ON COLUMN mcp_servers.tools IS '自动发现的工具列表';
COMMENT ON COLUMN mcp_servers.version IS 'Server 版本号';
COMMENT ON COLUMN mcp_servers.last_tested_at IS '最后测试连接时间';

-- --------------------------------------------------------------------------
-- 4.7 tool_configs — 工具配置表
-- --------------------------------------------------------------------------
CREATE TABLE tool_configs (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100)    NOT NULL,
    name_en         VARCHAR(100),
    icon            VARCHAR(50),
    description     TEXT,
    category        VARCHAR(50)     NOT NULL,
    category_label  VARCHAR(50),
    category_icon   VARCHAR(50),
    tool_type       VARCHAR(20)     NOT NULL DEFAULT 'builtin',
    endpoint        VARCHAR(500),
    config          JSONB,
    is_enabled      BOOLEAN         NOT NULL DEFAULT true,
    is_builtin      BOOLEAN         NOT NULL DEFAULT true,
    mcp_server_id   UUID            REFERENCES mcp_servers(id),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_tool_configs_category CHECK (category IN ('order', 'after_sale', 'user', 'custom', 'mcp')),
    CONSTRAINT ck_tool_configs_tool_type CHECK (tool_type IN ('builtin', 'mcp', 'custom'))
);

COMMENT ON TABLE  tool_configs IS '工具配置表（统一管理内置工具和 MCP 工具）';
COMMENT ON COLUMN tool_configs.name IS '工具名称（中文）';
COMMENT ON COLUMN tool_configs.name_en IS '英文名称';
COMMENT ON COLUMN tool_configs.category IS '分类：order / after_sale / user / custom';
COMMENT ON COLUMN tool_configs.category_label IS '分类显示名';
COMMENT ON COLUMN tool_configs.category_icon IS '分类图标';
COMMENT ON COLUMN tool_configs.tool_type IS '类型：builtin / mcp';
COMMENT ON COLUMN tool_configs.endpoint IS '自定义工具的 API 地址';
COMMENT ON COLUMN tool_configs.config IS '工具参数配置（JSON Schema 等）';
COMMENT ON COLUMN tool_configs.is_enabled IS '是否启用';
COMMENT ON COLUMN tool_configs.is_builtin IS '是否内置';
COMMENT ON COLUMN tool_configs.mcp_server_id IS '所属 MCP Server（MCP 工具）';

-- --------------------------------------------------------------------------
-- 4.8 agent_skills — Agent-Skill 关联表
-- --------------------------------------------------------------------------
CREATE TABLE agent_skills (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID            NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    skill_id        UUID            NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_agent_skills UNIQUE (agent_id, skill_id)
);

COMMENT ON TABLE  agent_skills IS 'Agent-Skill 多对多关联表';

-- --------------------------------------------------------------------------
-- 4.9 skill_resources — 技能资源文件表
-- --------------------------------------------------------------------------
CREATE TABLE skill_resources (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id        UUID            NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    file_name       VARCHAR(255)    NOT NULL,
    file_path       VARCHAR(500),
    file_size       BIGINT,
    mime_type       VARCHAR(100),
    file_content    TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

COMMENT ON TABLE  skill_resources IS '技能资源文件表';
COMMENT ON COLUMN skill_resources.skill_id IS '所属技能';
COMMENT ON COLUMN skill_resources.file_name IS '文件名';
COMMENT ON COLUMN skill_resources.file_path IS '文件存储路径';
COMMENT ON COLUMN skill_resources.file_size IS '文件大小（字节）';
COMMENT ON COLUMN skill_resources.mime_type IS 'MIME 类型';
COMMENT ON COLUMN skill_resources.file_content IS '资源文件文本内容（≤1MB完整存储，>1MB截断，二进制为NULL）';

-- --------------------------------------------------------------------------
-- 4.10 agent_mcp_servers — Agent-MCP Server 关联表
-- --------------------------------------------------------------------------
CREATE TABLE agent_mcp_servers (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID            NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    mcp_server_id   UUID            NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
    is_linked       BOOLEAN         NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_agent_mcp_servers UNIQUE (agent_id, mcp_server_id)
);

COMMENT ON TABLE  agent_mcp_servers IS 'Agent-MCP Server 多对多关联表';
COMMENT ON COLUMN agent_mcp_servers.is_linked IS '是否已连接';

-- --------------------------------------------------------------------------
-- 4.10 agent_tools — Agent-Tool 关联表
-- --------------------------------------------------------------------------
CREATE TABLE agent_tools (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID            NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    tool_config_id  UUID            NOT NULL REFERENCES tool_configs(id) ON DELETE CASCADE,
    is_enabled      BOOLEAN         NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_agent_tools UNIQUE (agent_id, tool_config_id)
);

COMMENT ON TABLE  agent_tools IS 'Agent-Tool 多对多关联表';
COMMENT ON COLUMN agent_tools.is_enabled IS '是否启用';

-- --------------------------------------------------------------------------
-- 4.11 agent_sub_agents — 主智能体-SubAgent关联表
-- --------------------------------------------------------------------------
CREATE TABLE agent_sub_agents (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_agent_id UUID            NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    sub_agent_id    UUID            NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_agent_sub_agents UNIQUE (parent_agent_id, sub_agent_id)
);

COMMENT ON TABLE agent_sub_agents IS '主智能体-SubAgent关联表';

-- --------------------------------------------------------------------------
-- 4.12 knowledge_documents — 知识库文档表
-- --------------------------------------------------------------------------
CREATE TABLE knowledge_documents (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name           VARCHAR(255)    NOT NULL,
    file_type           VARCHAR(20)     NOT NULL,
    file_size           BIGINT          NOT NULL,
    file_path           VARCHAR(500),
    vector_status       VARCHAR(20)     NOT NULL DEFAULT 'pending',
    vector_progress     INTEGER         NOT NULL DEFAULT 0,
    total_chunks        INTEGER         NOT NULL DEFAULT 0,
    processed_chunks    INTEGER         NOT NULL DEFAULT 0,
    error_message       TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_knowledge_docs_file_type CHECK (file_type IN ('pdf', 'docx', 'txt', 'md')),
    CONSTRAINT ck_knowledge_docs_vector_status CHECK (vector_status IN ('pending', 'processing', 'completed', 'failed'))
);

COMMENT ON TABLE  knowledge_documents IS '知识库文档表';
COMMENT ON COLUMN knowledge_documents.file_name IS '文档文件名';
COMMENT ON COLUMN knowledge_documents.file_type IS '文件类型：pdf / docx / txt / md';
COMMENT ON COLUMN knowledge_documents.file_size IS '文件大小（字节）';
COMMENT ON COLUMN knowledge_documents.file_path IS '文件存储路径';
COMMENT ON COLUMN knowledge_documents.vector_status IS '向量化状态：pending / processing / completed / failed';
COMMENT ON COLUMN knowledge_documents.vector_progress IS '向量化进度（0-100）';
COMMENT ON COLUMN knowledge_documents.total_chunks IS '总分块数';
COMMENT ON COLUMN knowledge_documents.processed_chunks IS '已处理分块数';
COMMENT ON COLUMN knowledge_documents.error_message IS '错误信息';

-- --------------------------------------------------------------------------
-- 4.13 document_chunks — 文档分块与向量表
-- --------------------------------------------------------------------------
CREATE TABLE document_chunks (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID            NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    content         TEXT            NOT NULL,
    embedding       vector(4096),
    chunk_index     INTEGER         NOT NULL,
    metadata        JSONB,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

COMMENT ON TABLE  document_chunks IS '文档分块与向量表（RAG 检索核心表）';
COMMENT ON COLUMN document_chunks.document_id IS '所属文档';
COMMENT ON COLUMN document_chunks.content IS '分块文本内容';
COMMENT ON COLUMN document_chunks.embedding IS '4096 维向量（nvidia/nv-embed-v1），如需更换模型请同步修改此维度';
COMMENT ON COLUMN document_chunks.chunk_index IS '分块序号（从 0 开始）';
COMMENT ON COLUMN document_chunks.metadata IS '元数据（页码、章节标题等）';

-- --------------------------------------------------------------------------
-- 4.14 knowledge_qa — 知识库 Q&A 表
-- --------------------------------------------------------------------------
CREATE TABLE knowledge_qa (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    question        TEXT            NOT NULL,
    answer          TEXT            NOT NULL,
    embedding       vector(4096),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

COMMENT ON TABLE  knowledge_qa IS '知识库 Q&A 表';
COMMENT ON COLUMN knowledge_qa.embedding IS '4096 维向量（nvidia/nv-embed-v1），如需更换模型请同步修改此维度';
COMMENT ON COLUMN knowledge_qa.question IS '问题';
COMMENT ON COLUMN knowledge_qa.answer IS '答案';

-- --------------------------------------------------------------------------
-- 4.15 agent_knowledge_documents — Agent-知识库文档关联表
-- --------------------------------------------------------------------------
CREATE TABLE agent_knowledge_documents (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID            NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    document_id     UUID            NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_agent_knowledge_documents UNIQUE (agent_id, document_id)
);

COMMENT ON TABLE  agent_knowledge_documents IS 'Agent-知识库文档关联表';

-- --------------------------------------------------------------------------
-- 4.16 agent_knowledge_qa — Agent-QA关联表
-- --------------------------------------------------------------------------
CREATE TABLE agent_knowledge_qa (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID            NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    qa_id           UUID            NOT NULL REFERENCES knowledge_qa(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_agent_knowledge_qa UNIQUE (agent_id, qa_id)
);

COMMENT ON TABLE  agent_knowledge_qa IS 'Agent-QA关联表';

-- --------------------------------------------------------------------------
-- 4.17 conversations — 对话会话表
-- --------------------------------------------------------------------------
CREATE TABLE conversations (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      VARCHAR(100)    NOT NULL,
    user_id         VARCHAR(100),
    user_name       VARCHAR(100),
    user_avatar     VARCHAR(500),
    status          VARCHAR(20)     NOT NULL DEFAULT 'active',
    intent          VARCHAR(50),
    handled_by      VARCHAR(20)     NOT NULL DEFAULT 'agent',
    message_count   INTEGER         NOT NULL DEFAULT 0,
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    ended_at        TIMESTAMPTZ,
    channel         VARCHAR(20)     NOT NULL DEFAULT 'web',
    feishu_open_id  VARCHAR(100),
    feishu_chat_id  VARCHAR(100),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_conversations_status CHECK (status IN ('active', 'resolved', 'transferred', 'pending')),
    CONSTRAINT ck_conversations_handled_by CHECK (handled_by IN ('agent', 'human')),
    CONSTRAINT ck_conversations_channel CHECK (channel IN ('web', 'feishu'))
);

COMMENT ON TABLE  conversations IS '对话会话表';
COMMENT ON COLUMN conversations.id IS '对话 ID（同时作为 LangGraph thread_id）';
COMMENT ON COLUMN conversations.session_id IS '用户端会话标识（浏览器生成，用于会话恢复）';
COMMENT ON COLUMN conversations.user_id IS '终端用户标识（可选，匿名用户为 NULL）';
COMMENT ON COLUMN conversations.user_name IS '终端用户显示名';
COMMENT ON COLUMN conversations.user_avatar IS '终端用户头像';
COMMENT ON COLUMN conversations.status IS '状态：active / resolved / transferred / pending';
COMMENT ON COLUMN conversations.intent IS '识别到的意图';
COMMENT ON COLUMN conversations.handled_by IS '处理方：agent / human';
COMMENT ON COLUMN conversations.message_count IS '消息总数';
COMMENT ON COLUMN conversations.started_at IS '开始时间';
COMMENT ON COLUMN conversations.ended_at IS '结束时间';
COMMENT ON COLUMN conversations.channel IS '消息渠道：web / feishu';
COMMENT ON COLUMN conversations.feishu_open_id IS '飞书用户 open_id（飞书渠道）';
COMMENT ON COLUMN conversations.feishu_chat_id IS '飞书会话 chat_id（飞书渠道）';

-- --------------------------------------------------------------------------
-- 4.18 messages — 消息表
-- --------------------------------------------------------------------------
CREATE TABLE messages (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID            NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role                VARCHAR(20)     NOT NULL,
    content             TEXT            NOT NULL,
    agent_id            UUID            REFERENCES agents(id),
    agent_name          VARCHAR(100),
    tool_calls          JSONB,
    is_system_message   BOOLEAN         NOT NULL DEFAULT false,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_messages_role CHECK (role IN ('user', 'agent', 'system', 'human_agent'))
);

COMMENT ON TABLE  messages IS '消息表';
COMMENT ON COLUMN messages.conversation_id IS '所属对话';
COMMENT ON COLUMN messages.role IS '角色：user / agent / system / human_agent';
COMMENT ON COLUMN messages.content IS '消息内容';
COMMENT ON COLUMN messages.agent_id IS '产生消息的 Agent';
COMMENT ON COLUMN messages.agent_name IS 'Agent 名称（冗余存储）';
COMMENT ON COLUMN messages.tool_calls IS '工具调用记录 JSONB';
COMMENT ON COLUMN messages.is_system_message IS '是否系统消息';

-- --------------------------------------------------------------------------
-- 4.19 human_sessions — 人工客服会话表
-- --------------------------------------------------------------------------
CREATE TABLE human_sessions (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID            NOT NULL REFERENCES conversations(id),
    agent_id        UUID            REFERENCES agents(id),
    status          VARCHAR(20)     NOT NULL DEFAULT 'waiting',
    operator_id     UUID            REFERENCES users(id),
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    ended_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_human_sessions_conversation UNIQUE (conversation_id),
    CONSTRAINT ck_human_sessions_status CHECK (status IN ('waiting', 'active', 'ended'))
);

COMMENT ON TABLE  human_sessions IS '人工客服会话表';
COMMENT ON COLUMN human_sessions.conversation_id IS '关联对话';
COMMENT ON COLUMN human_sessions.agent_id IS '触发转人工的 Agent';
COMMENT ON COLUMN human_sessions.status IS '状态：waiting / active / ended';
COMMENT ON COLUMN human_sessions.operator_id IS '接手的客服人员';
COMMENT ON COLUMN human_sessions.started_at IS '开始时间';
COMMENT ON COLUMN human_sessions.ended_at IS '结束时间';

-- --------------------------------------------------------------------------
-- 4.20 quick_replies — 快捷回复表
-- --------------------------------------------------------------------------
CREATE TABLE quick_replies (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(200)    NOT NULL,
    content         TEXT            NOT NULL,
    category        VARCHAR(50),
    sort_order      INTEGER         NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

COMMENT ON TABLE  quick_replies IS '快捷回复表';
COMMENT ON COLUMN quick_replies.title IS '标题';
COMMENT ON COLUMN quick_replies.content IS '回复内容';
COMMENT ON COLUMN quick_replies.category IS '分类';
COMMENT ON COLUMN quick_replies.sort_order IS '排序序号';

-- --------------------------------------------------------------------------
-- 4.21 settings — 系统设置表
-- --------------------------------------------------------------------------
CREATE TABLE settings (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    category        VARCHAR(50)     NOT NULL,
    key             VARCHAR(100)    NOT NULL,
    value           JSONB           NOT NULL,
    description     VARCHAR(255),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uk_settings_category_key UNIQUE (category, key)
);

COMMENT ON TABLE  settings IS '系统设置表（KV 结构）';
COMMENT ON COLUMN settings.category IS '设置分类：appearance / notifications / chat_widget / about';
COMMENT ON COLUMN settings.key IS '设置键名';
COMMENT ON COLUMN settings.value IS '设置值（JSONB）';
COMMENT ON COLUMN settings.description IS '设置说明';

-- ============================================================================
-- Part 5: 创建索引
-- ============================================================================

-- 5.1 users 索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email    ON users(email);
CREATE INDEX idx_users_phone    ON users(phone);
CREATE INDEX idx_users_status   ON users(status);

-- 5.2 refresh_tokens 索引
CREATE INDEX idx_refresh_tokens_user_id    ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- 5.3 model_configs 索引
CREATE INDEX idx_model_configs_name   ON model_configs(name);
CREATE INDEX idx_model_configs_status ON model_configs(status);

-- 5.4 agents 索引
CREATE INDEX idx_agents_type       ON agents(type);
CREATE INDEX idx_agents_is_enabled ON agents(is_enabled);
CREATE INDEX idx_agents_human_agent_id ON agents(human_agent_id);

-- 5.5 agent_sub_agents 索引
CREATE INDEX idx_agent_sub_agents_parent ON agent_sub_agents(parent_agent_id);
CREATE INDEX idx_agent_sub_agents_sub ON agent_sub_agents(sub_agent_id);

-- 5.6 agent_knowledge_documents 索引
CREATE INDEX idx_agent_knowledge_documents_agent ON agent_knowledge_documents(agent_id);
CREATE INDEX idx_agent_knowledge_documents_document ON agent_knowledge_documents(document_id);

-- 5.7 agent_knowledge_qa 索引
CREATE INDEX idx_agent_knowledge_qa_agent ON agent_knowledge_qa(agent_id);
CREATE INDEX idx_agent_knowledge_qa_qa ON agent_knowledge_qa(qa_id);

-- 5.8 skills 索引
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_status   ON skills(status);
CREATE INDEX idx_skills_tags     ON skills USING gin (tags);

-- 5.9 skill_resources 索引
CREATE INDEX idx_skill_resources_skill_id ON skill_resources(skill_id);

-- 5.10 tool_configs 索引
CREATE INDEX idx_tool_configs_category ON tool_configs(category);
CREATE INDEX idx_tool_configs_tool_type ON tool_configs(tool_type);

-- 5.10 mcp_servers 索引
CREATE INDEX idx_mcp_servers_status ON mcp_servers(status);
CREATE INDEX idx_mcp_servers_is_enabled ON mcp_servers(is_enabled);

-- 5.11 knowledge_documents 索引
CREATE INDEX idx_knowledge_docs_vector_status ON knowledge_documents(vector_status);

-- 5.12 document_chunks 索引
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);

-- 5.13 document_chunks HNSW 向量索引（语义检索核心索引）
-- nvidia/nv-embed-v1 输出 4096 维向量
-- pgvector 0.8.0+ 支持最大 16000 维 HNSW 索引，请确保 pgvector 版本 ≥ 0.8.0
-- CREATE INDEX idx_document_chunks_embedding
--     ON document_chunks
--     USING hnsw (embedding vector_cosine_ops);

-- 5.14 knowledge_qa 索引
CREATE INDEX idx_knowledge_qa_question_trgm
    ON knowledge_qa
    USING gin (question gin_trgm_ops);

-- 5.15 knowledge_qa HNSW 向量索引（QA 语义匹配）
-- nvidia/nv-embed-v1 输出 4096 维向量
-- pgvector 0.8.0+ 支持最大 16000 维 HNSW 索引，请确保 pgvector 版本 ≥ 0.8.0
-- CREATE INDEX idx_knowledge_qa_embedding
--     ON knowledge_qa
--     USING hnsw (embedding vector_cosine_ops);

-- 5.16 conversations 索引
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_status     ON conversations(status);
CREATE INDEX idx_conversations_started_at ON conversations(started_at);
CREATE INDEX idx_conversations_intent     ON conversations(intent);
CREATE INDEX idx_conversations_channel         ON conversations(channel);
CREATE INDEX idx_conversations_feishu_open_id  ON conversations(feishu_open_id);

-- 5.17 messages 索引
CREATE INDEX idx_messages_conversation_id_created_at ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_created_at               ON messages(created_at);

-- 5.18 human_sessions 索引
CREATE INDEX idx_human_sessions_status          ON human_sessions(status);
CREATE INDEX idx_human_sessions_operator_id     ON human_sessions(operator_id);
CREATE INDEX idx_human_sessions_conversation_id ON human_sessions(conversation_id);

-- 5.19 quick_replies 索引
CREATE INDEX idx_quick_replies_category ON quick_replies(category);

-- ============================================================================
-- Part 6: 创建触发器
-- ============================================================================

-- 为所有包含 updated_at 字段的表创建自动更新触发器

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_refresh_tokens_updated_at
    BEFORE UPDATE ON refresh_tokens
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_model_configs_updated_at
    BEFORE UPDATE ON model_configs
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_skills_updated_at
    BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_mcp_servers_updated_at
    BEFORE UPDATE ON mcp_servers
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_tool_configs_updated_at
    BEFORE UPDATE ON tool_configs
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_agent_mcp_servers_updated_at
    BEFORE UPDATE ON agent_mcp_servers
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_agent_tools_updated_at
    BEFORE UPDATE ON agent_tools
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_agent_sub_agents_updated_at
    BEFORE UPDATE ON agent_sub_agents
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_agent_knowledge_documents_updated_at
    BEFORE UPDATE ON agent_knowledge_documents
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_agent_knowledge_qa_updated_at
    BEFORE UPDATE ON agent_knowledge_qa
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_knowledge_documents_updated_at
    BEFORE UPDATE ON knowledge_documents
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_knowledge_qa_updated_at
    BEFORE UPDATE ON knowledge_qa
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_human_sessions_updated_at
    BEFORE UPDATE ON human_sessions
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_quick_replies_updated_at
    BEFORE UPDATE ON quick_replies
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 完成
-- ============================================================================
-- 数据库初始化完成。
-- 共创建 22 张业务表、36 个 B-tree 索引、2 个 HNSW 向量索引、2 个 GIN 索引、18 个触发器。
-- LangGraph checkpoint 表由应用层 PostgresSaver.setup() 自动创建。
-- 注：以上仅包含 PostgreSQL 业务表，完整数据架构包含 7 种数据库存储。
--
-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  下一步：执行种子数据脚本                                              ║
-- ╠══════════════════════════════════════════════════════════════════════════╣
-- ║                                                                          ║
-- ║  init.sql 仅负责建表，不包含业务数据。如需初始化测试环境数据，          ║
-- ║  请执行 seed.sql 脚本：                                                  ║
-- ║                                                                          ║
-- ║    psql -U tianting -d tianting -f database/seed.sql                     ║
-- ║                                                                          ║
-- ║  seed.sql 包含以下初始数据：                                             ║
-- ║    - 基础账号（Administrator + Operator）                              ║
-- ║    - 系统基础设置                                                         ║
-- ║    - 模型配置（ModelConfig）—— 需手动填入真实 API Key                   ║
-- ║    - 主智能体 Orchestrator + 子智能体 QA_Agent                          ║
-- ║    - 智能体关联关系                                                     ║
-- ║    - 快捷回复                                                           ║
-- ║    - 内置Skills                                                         ║
-- ║    - 内置工具                                                            ║
-- ║    - 知识库/QA 关联指引（注释说明，需手动操作）                          ║
-- ║                                                                          ║
-- ║  执行 seed.sql 后，必须登录 Admin UI 填入真实的模型 API Key，           ║
-- ║  否则飞书消息链路无法正常工作。                                          ║
-- ║                                                                          ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
-- ============================================================================
