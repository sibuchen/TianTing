-- ============================================================================
-- TianTing Snowflake Analysis Query Templates
-- 天听系统 Snowflake 预定义分析查询模板
-- ============================================================================

USE DATABASE TIANTING_RAW;

-- 1. 用户活跃度分析（按日统计）
SELECT
    metric_date,
    active_users,
    total_conversations,
    resolution_rate
FROM ANALYTICS.daily_metrics
WHERE metric_date >= DATEADD(DAY, -30, CURRENT_DATE())
ORDER BY metric_date DESC;

-- 2. Agent 使用排行（Top 10）
SELECT
    agent_name,
    SUM(total_sessions) AS total_sessions,
    AVG(resolution_rate) AS avg_resolution_rate,
    AVG(avg_operation_duration_ms) AS avg_duration_ms
FROM ANALYTICS.agent_perf
WHERE metric_date >= DATEADD(DAY, -30, CURRENT_DATE())
GROUP BY agent_name
ORDER BY total_sessions DESC
LIMIT 10;

-- 3. 意图趋势分析
SELECT
    metric_date,
    intent,
    session_count,
    resolution_rate
FROM ANALYTICS.intent_trends
WHERE metric_date >= DATEADD(DAY, -7, CURRENT_DATE())
ORDER BY metric_date DESC, session_count DESC;

-- 4. 响应时长分布（按Agent）
SELECT
    agent_name,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) AS p50_duration_ms,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY duration_ms) AS p90_duration_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) AS p99_duration_ms,
    AVG(duration_ms) AS avg_duration_ms,
    COUNT(*) AS total_operations
FROM RAW.operation_logs
WHERE created_at >= DATEADD(DAY, -7, CURRENT_DATE())
  AND duration_ms IS NOT NULL
GROUP BY agent_name
ORDER BY total_operations DESC;

-- 5. 对话漏斗分析
SELECT
    metric_date,
    started,
    engaged,
    transferred,
    resolved,
    completion_rate,
    ROUND(engaged * 100.0 / NULLIF(started, 0), 1) AS engagement_rate,
    ROUND(transferred * 100.0 / NULLIF(started, 0), 1) AS transfer_rate
FROM ANALYTICS.funnel_analysis
WHERE metric_date >= DATEADD(DAY, -30, CURRENT_DATE())
ORDER BY metric_date DESC;

-- 6. 按渠道的对话分布
SELECT
    channel,
    COUNT(*) AS total_conversations,
    ROUND(AVG(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) * 100, 1) AS resolution_rate,
    COUNT(DISTINCT user_id) AS unique_users
FROM RAW.conversations
WHERE started_at >= DATEADD(DAY, -30, CURRENT_DATE())
GROUP BY channel
ORDER BY total_conversations DESC;

-- 7. 用户活跃时段分析（按小时）
SELECT
    HOUR(started_at) AS hour_of_day,
    COUNT(*) AS conversation_count,
    COUNT(DISTINCT user_id) AS unique_users
FROM RAW.conversations
WHERE started_at >= DATEADD(DAY, -30, CURRENT_DATE())
GROUP BY HOUR(started_at)
ORDER BY hour_of_day;