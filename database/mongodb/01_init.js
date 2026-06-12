// ============================================================================
// TianTing MongoDB Initialization
// 天听系统 MongoDB 数据库初始化
// ============================================================================

db = db.getSiblingDB('tianting');

db.createCollection('agent_operation_logs');
db.agent_operation_logs.createIndex(
    { conversation_id: 1, created_at: -1 },
    { name: 'idx_conv_time' }
);
db.agent_operation_logs.createIndex(
    { agent_id: 1, created_at: -1 },
    { name: 'idx_agent_time' }
);
db.agent_operation_logs.createIndex(
    { operation_type: 1, created_at: -1 },
    { name: 'idx_optype_time' }
);
db.agent_operation_logs.createIndex(
    { created_at: -1 },
    { name: 'idx_created_at' }
);

db.createCollection('conversation_events');
db.conversation_events.createIndex(
    { conversation_id: 1, created_at: -1 },
    { name: 'idx_conv_time' }
);
db.conversation_events.createIndex(
    { event_type: 1, created_at: -1 },
    { name: 'idx_event_time' }
);
db.conversation_events.createIndex(
    { created_at: -1 },
    { name: 'idx_created_at' }
);

db.createCollection('conversation_transcripts');
db.conversation_transcripts.createIndex(
    { conversation_id: 1 },
    { name: 'idx_conversation_id', unique: true }
);
db.conversation_transcripts.createIndex(
    { created_at: -1 },
    { name: 'idx_created_at' }
);

print('TianTing MongoDB initialization completed.');