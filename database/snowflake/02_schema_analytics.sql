-- ============================================================================
-- TianTing Snowflake ANALYTICS Layer
-- 天听系统 Snowflake 分析层：物化视图
-- ============================================================================

USE DATABASE TIANTING_RAW;
CREATE SCHEMA IF NOT EXISTS ANALYTICS;
USE SCHEMA ANALYTICS;

CREATE OR REPLACE MATERIALIZED VIEW daily_metrics AS
SELECT
    DATE(started_at) AS metric_date,
    COUNT(DISTINCT id) AS total_conversations,
    COUNT(DISTINCT CASE WHEN status = 'resolved' THEN id END) AS resolved_conversations,
    ROUND(
        COUNT(DISTINCT CASE WHEN status = 'resolved' THEN id END) * 100.0
        / NULLIF(COUNT(DISTINCT id), 0), 1
    ) AS resolution_rate,
    COUNT(DISTINCT agent_id) AS active_agents,
    COUNT(DISTINCT user_id) AS active_users
FROM RAW.conversations
GROUP BY DATE(started_at);

CREATE OR REPLACE MATERIALIZED VIEW agent_perf AS
SELECT
    c.agent_id,
    c.agent_name,
    DATE(c.started_at) AS metric_date,
    COUNT(DISTINCT c.id) AS total_sessions,
    COUNT(DISTINCT CASE WHEN c.status = 'resolved' THEN c.id END) AS resolved_sessions,
    ROUND(
        COUNT(DISTINCT CASE WHEN c.status = 'resolved' THEN c.id END) * 100.0
        / NULLIF(COUNT(DISTINCT c.id), 0), 1
    ) AS resolution_rate,
    AVG(ol.duration_ms) AS avg_operation_duration_ms
FROM RAW.conversations c
LEFT JOIN RAW.operation_logs ol ON c.id = ol.conversation_id
GROUP BY c.agent_id, c.agent_name, DATE(c.started_at);

CREATE OR REPLACE MATERIALIZED VIEW intent_trends AS
SELECT
    DATE(started_at) AS metric_date,
    intent,
    COUNT(*) AS session_count,
    COUNT(DISTINCT user_id) AS unique_users,
    ROUND(
        COUNT(CASE WHEN status = 'resolved' THEN 1 END) * 100.0
        / NULLIF(COUNT(*), 0), 1
    ) AS resolution_rate
FROM RAW.conversations
WHERE intent IS NOT NULL
GROUP BY DATE(started_at), intent;

CREATE OR REPLACE MATERIALIZED VIEW funnel_analysis AS
SELECT
    DATE(started_at) AS metric_date,
    COUNT(*) AS started,
    COUNT(CASE WHEN status IN ('active', 'transferred', 'resolved') THEN 1 END) AS engaged,
    COUNT(CASE WHEN status = 'transferred' THEN 1 END) AS transferred,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) AS resolved,
    ROUND(
        COUNT(CASE WHEN status = 'resolved' THEN 1 END) * 100.0
        / NULLIF(COUNT(*), 0), 1
    ) AS completion_rate
FROM RAW.conversations
GROUP BY DATE(started_at);