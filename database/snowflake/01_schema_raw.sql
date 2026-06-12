-- ============================================================================
-- TianTing Snowflake RAW Layer Schema
-- 天听系统 Snowflake 原始数据层表结构
-- ============================================================================

CREATE DATABASE IF NOT EXISTS TIANTING_RAW;
USE DATABASE TIANTING_RAW;
CREATE SCHEMA IF NOT EXISTS RAW;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS conversations (
    id              VARCHAR(36) PRIMARY KEY,
    agent_id        VARCHAR(36),
    agent_name      VARCHAR(255),
    user_id         VARCHAR(36),
    user_name       VARCHAR(255),
    user_avatar     VARCHAR(500),
    session_id      VARCHAR(255),
    channel         VARCHAR(50) DEFAULT 'web',
    intent          VARCHAR(255),
    status          VARCHAR(50) DEFAULT 'active',
    handled_by      VARCHAR(50) DEFAULT 'agent',
    resolution_note TEXT,
    started_at      TIMESTAMP_NTZ,
    ended_at        TIMESTAMP_NTZ,
    created_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS messages (
    id              VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(id),
    role            VARCHAR(50) NOT NULL,
    content         TEXT,
    agent_name      VARCHAR(255),
    tool_calls      VARIANT,
    created_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS agent_usage (
    usage_date      DATE,
    agent_id        VARCHAR(36),
    agent_name      VARCHAR(255),
    agent_type      VARCHAR(100),
    total_sessions  INTEGER DEFAULT 0,
    resolved_sessions INTEGER DEFAULT 0,
    avg_response_ms FLOAT DEFAULT 0,
    PRIMARY KEY (usage_date, agent_id)
);

CREATE TABLE IF NOT EXISTS operation_logs (
    log_id          VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36),
    agent_id        VARCHAR(36),
    agent_name      VARCHAR(255),
    operation_type  VARCHAR(100),
    operation_detail VARIANT,
    parent_log_id   VARCHAR(36),
    duration_ms     INTEGER,
    created_at      TIMESTAMP_NTZ
);