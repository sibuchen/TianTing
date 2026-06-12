# TianTing（天听）智能客服系统 — 项目介绍
<div align="center">

**基于 LangGraph 的 multi-agents 客服系统**
<!-- 静态徽章 https://img.shields.io/badge/<左侧文字>-<右侧文字>-<颜色> -->
[![License](https://img.shields.io/badge/License-GPLv3-D6336C.svg?logo=GPLv3&logoColor=BD0000)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub](https://img.shields.io/badge/GitHub-TianTing-181717?logo=github&logoColor=181717)](https://github.com/sibuchen/TianTing)
[![Author](https://img.shields.io/badge/Author-sibuchen-orange?logo=github&logoColor=181717)](https://github.com/sibuchen/)

</div>
## 一、项目概述

TianTing 是一个**企业级 AI 智能客服平台**，支持多渠道接入（Web 网页、飞书 IM），采用 Agent 编排架构实现意图识别与自动路由，结合 RAG 检索增强、知识图谱、MCP 工具调用和人工客服转接，为用户提供端到端的智能问答服务。

项目采用**前后端分离 + Docker 容器化**部署，后端基于 Python FastAPI，前端基于 Next.js (React)，通过 Nginx 网关统一入口。

---

## 二、技术架构

### 2.1 整体架构图

```
用户端（Web / 飞书）
       │
       ▼
   Nginx Gateway (:3534)
       │
   ┌───┴───┐
   ▼       ▼
Next.js   FastAPI (:2811)
(frontend)    │
              ├── Agent Runtime (LangChain + LangGraph)
              │      ├── Orchestrator（编排器）
              │      ├── FAQ Agent / After-sale Agent / Custom Agent
              │      ├── Sub-Agent 调用链
              │      └── MCP 工具执行
              │
              ├── RAG Pipeline
              │      ├── Embedder (NVIDIA nv-embed-v1 / OpenAI Compatible)
              │      ├── Retriever (pgvector cosine + Qdrant fallback)
              │      └── QA Search (向量优先 + ILIKE 兜底)
              │
              ├── Knowledge Graph (Neo4j)
              │      ├── Agent-Skill-Tool 关系图
              │      └── User-Conversation-Agent 关系图
              │
              └── IM Channel Adapter
                     ├── WebAdapter（WebSocket）
                     └── FeishuAdapter（Lark SDK）

数据层：
  PostgreSQL (pgvector) — 主数据 + 向量存储
  Redis — 缓存 / 限频 / ARQ 异步任务队列
  Qdrant — 高性能向量检索
  Neo4j — 知识图谱
  MongoDB — 对话日志 / 非结构化数据
```

### 2.2 技术栈

| 层级 | 技术选型 |
|------|---------|
| **前端** | Next.js 14 (App Router)、React、TypeScript、Zustand 状态管理、next-intl 国际化、pnpm |
| **后端** | Python 3.12、FastAPI、SQLAlchemy 2.0 (async)、Pydantic v2 |
| **AI 框架** | LangChain、LangGraph、OpenAI Compatible API |
| **向量存储** | pgvector (PostgreSQL) + Qdrant（双引擎，Qdrant 优先） |
| **知识图谱** | Neo4j 5 + APOC |
| **消息队列** | Redis (ARQ 异步任务) |
| **日志存储** | MongoDB 7 |
| **IM 集成** | 飞书 Lark SDK (lark-oapi) |
| **安全** | JWT (access + refresh token)、AES-256-GCM (API Key 加密)、bcrypt 密码哈希 |
| **部署** | Docker Compose、Nginx 反向代理 |

---

## 三、核心模块详解

### 3.1 Agent 编排系统

这是天听的核心引擎。系统采用**编排器 + 子 Agent** 的多智能体架构：

- **Orchestrator（编排器）**：作为入口 Agent，负责意图识别和任务路由。编排器通过 LLM Tool Calling 机制，自主决定是直接回复用户，还是调用子 Agent 处理特定问题。
- **专业 Agent**：包括 FAQ Agent（常见问题）、After-sale Agent（售后处理）、Custom Agent（自定义），每种 Agent 拥有独立的 System Prompt、模型配置、技能和工具。
- **Sub-Agent 调用链**：编排器通过 `call_subagent_*` 工具动态调用子 Agent，子 Agent 的返回结果作为上下文回传给编排器，形成多轮推理循环（最多 8 轮）。
- **人工转接**：双重触发机制 —— 关键词匹配（`transfer_keywords`）和 LLM 判断（`transfer_to_human` 工具调用），转接时自动创建 `HumanSession` 进入等待队列。

**Agent Runtime 核心流程**（`agents/runtime/runtime.py`）：

```
用户消息 → 查找 Orchestrator → 检查转接关键词
                                      │
                    ┌─────────────────┤
                    ▼                 ▼
              直接转人工        构建 System Prompt
                                (技能元数据 + 工具描述)
                                      │
                                      ▼
                              LLM 推理循环 (最多8轮)
                              ┌──────────────┐
                              │ Tool Calls?  │
                              │  是 → 并行执行│→ 结果回注上下文 → 继续循环
                              │  否 → 返回文本│→ 结束
                              └──────────────┘
```

**支持的 Agent 类型**（`models/agent.py`）：

- `orchestrator` — 编排器，全局唯一入口
- `faq` — FAQ 问答
- `after-sale` — 售后处理
- `custom` — 自定义场景

**Agent 可配置能力**：

- System Prompt（最大 5000 字符）
- 模型配置（关联 ModelConfig，支持多 LLM Provider）
- Skills（技能，多对多关联）
- MCP Servers（外部工具服务）
- Tools（内置工具 + MCP 工具，可启用/禁用）
- 知识库（文档 + QA 对，向量化后用于 RAG 检索）
- 子 Agent 编排关系

### 3.2 MCP 工具系统

天听实现了完整的 **Model Context Protocol (MCP) 客户端**（`agents/mcp_client.py`），支持两种传输模式：

- **SSE 模式**：通过 HTTP 连接远程 MCP Server，获取工具列表
- **stdio 模式**：通过子进程启动本地 MCP Server，使用 JSON-RPC 2.0 协议通信（支持 `initialize` 握手、`tools/list` 发现、`tools/call` 执行）

每个 Agent 可关联多个 MCP Server，工具在运行时自动发现并注入到 LLM 的 Tool Calling 上下文中。

**工具执行流程**：

```
LLM 返回 tool_calls
       │
       ▼
解析工具名称
       │
       ├── call_subagent_* → 调用子 Agent Runtime
       ├── transfer_to_human → 触发人工转接
       └── MCP 工具 → MCPClient._execute_tool → 转发到对应 MCP Server
```

工具支持并行执行（`_execute_tool_calls_parallel`），并标注只读/危险属性。

### 3.3 RAG 检索增强系统

天听实现了完整的 RAG Pipeline，支持**文档检索**和 **QA 检索**两条路径：

**文档检索链路**（`rag/`）：

1. **Embedder**（`embedder.py`）：调用 Embedding API（默认 NVIDIA nv-embed-v1，4096 维），支持单条/批量文本向量化，内置文本分块（chunk_size=500, overlap=50）
2. **Qdrant Client**（`qdrant_client.py`）：管理两个 Collection —— `document_chunks`（文档块）和 `knowledge_qa`（QA 对），提供 upsert/search/delete 操作
3. **Retriever**（`retriever.py`）：Qdrant 优先检索，pgvector cosine_distance 兜底；支持混合检索（`hybrid_search`）和重排序（`rerank`）

**QA 检索链路**（`rag/qa_search.py`）：

- 向量语义检索优先（Qdrant → pgvector）
- Embedding 失败时自动降级为 ILIKE 关键词匹配
- 关键词匹配时计算相关性分数（子串匹配 + 词重叠率）

**降级策略设计**：

```
Qdrant 可用? → 是 → Qdrant 语义检索
    │ 否
    ▼
pgvector 可用? → 是 → pgvector cosine 检索
    │ 否
    ▼
ILIKE 关键词匹配兜底
```

### 3.4 知识图谱系统

基于 Neo4j 构建 Agent 关系图谱（`graph/`）：

**图谱节点类型**：

- `Agent` — 智能体（属性：id, name, type, is_enabled）
- `Skill` — 技能
- `Tool` — 工具
- `KnowledgeDocument` — 知识文档
- `KnowledgeQA` — 问答对
- `User` — 用户
- `Conversation` — 对话

**关系类型**：

- `Agent -[:HAS_SUB_AGENT]-> Agent`
- `Agent -[:HAS_SKILL]-> Skill`
- `Agent -[:HAS_TOOL]-> Tool`
- `Agent -[:HAS_KNOWLEDGE_DOC]-> KnowledgeDocument`
- `Agent -[:HAS_QA]-> KnowledgeQA`
- `User -[:INITIATED]-> Conversation`
- `Conversation -[:HANDLED_BY]-> Agent`

**同步策略**：应用启动时执行 `full_sync`（清空 + 全量同步），运行时通过 `sync_service` 增量同步变更。

### 3.5 多渠道 IM 系统

采用**适配器模式**设计（`im/`），支持渠道无缝扩展：

```
IMAdapter (ABC)          IMClient (ABC)
    │                        │
    ├── WebAdapter           ├── FeishuClient
    └── FeishuAdapter        └── ...
```

- **IncomingMessage**：统一消息模型（channel, content, user_id, session_id, extra）
- **IMAdapter**：抽象接口（`send_message`, `send_streaming_message`, `channel_name`）
- **IMClient**：底层客户端抽象
- **Channel Registry**：渠道注册表，运行时动态创建适配器实例

**飞书集成**（`im/feishu/`）：

- 基于 `lark-oapi` SDK，支持 Webhook 和 WebSocket 两种事件接收模式
- 实现消息发送、回复、用户名查询
- Webhook 模式：Token 验签 + 事件分发

### 3.6 人工客服系统

当 Agent 无法处理时，支持**无缝转接人工客服**：

**数据模型**：

- `HumanSession`：人工客服会话（状态流转：waiting → active → ended）
- `Conversation`：对话会话（状态：active / transferred / resolved / pending）

**核心流程**：

```
Agent 判断需要转人工
       │
       ▼
创建 HumanSession (status=waiting)
Conversation.status → "transferred"
       │
       ▼
WebSocket 推送 admin 频道
管理员看到等待队列
       │
       ▼
客服点击「接手」
HumanSession.status → "active"
       │
       ▼
客服通过 WebSocket 与用户实时对话
支持快捷回复
       │
       ▼
结束会话
HumanSession.status → "ended"
Conversation.status → "resolved"
```

**API 接口**（`api/admin/human_service.py`）：

- `GET /queue` — 获取等待队列（含当前客服的活跃对话）
- `POST /accept` — 接手对话
- `POST /messages` — 客服发送消息
- `POST /end` — 结束会话
- `GET /quick-replies` — 快捷回复模板

### 3.7 实时通信系统

基于 WebSocket 实现双向实时通信（`ws/`）：

- **Admin WebSocket** (`/ws/admin`)：管理员后台实时推送 —— 新对话通知、对话状态变更、实时统计数据
- **Chat WebSocket** (`/ws/chat/{session_id}`)：用户聊天实时消息推送

**ChannelManager** 实现发布-订阅模式：

- `publish_realtime_status` — 推送实时统计
- `publish_new_conversation` — 推送新对话
- `publish_conversation_update` — 推送对话更新
- `publish_message` — 推送聊天消息

### 3.8 安全与认证系统

**认证体系**（`core/security.py`）：

- JWT 双 Token 机制：Access Token（24h / 记住我 30d）+ Refresh Token（7d / 30d）
- bcrypt 密码哈希（12 轮）
- AES-256-GCM 加密存储 LLM API Key
- Token 掩码显示

**API 安全**：

- CORS 跨域控制
- 请求限频（通用 60/min，聊天 30/min）
- CAPTCHA 验证码（`core/captcha.py`）
- 自定义异常体系（`core/exceptions.py`，110 个符号定义）

### 3.9 管理后台（前端）

基于 Next.js App Router 的管理后台（`frontend/src/app/(admin)/`）：

| 页面 | 功能 |
|------|------|
| `/dashboard` | 仪表盘 —— 实时统计、意图分布、渠道分布、最近对话 |
| `/agents` | Agent 管理 —— 创建/编辑/删除 Agent，配置 Prompt、模型、技能、工具、知识库、子 Agent |
| `/knowledge` | 知识库管理 —— 文档上传/向量化、QA 对管理 |
| `/tools` | 工具管理 —— 内置工具 + MCP 工具配置 |
| `/skills` | 技能管理 —— Agent 技能的创建与配置 |
| `/human-service` | 人工客服 —— 等待队列、实时对话、快捷回复 |
| `/history` | 历史记录 —— 对话历史浏览与搜索 |
| `/users` | 用户管理 —— 管理员账号管理 |
| `/api-keys` | API 密钥管理 —— LLM Provider API Key 加密存储 |
| `/settings` | 系统设置 |

---

## 四、数据模型设计

### 4.1 核心实体关系

```
User ──────┐
           │
ModelConfig ── Agent (orchestrator/faq/after-sale/custom)
                │
                ├── AgentSkill ─── Skill
                ├── AgentTool ─── ToolConfig
                ├── AgentMCPServer ─── MCPServerConfig
                ├── AgentSubAgent ─── Agent (子Agent)
                ├── AgentKnowledgeDocument ─── KnowledgeDocument
                │                              └── DocumentChunk (向量化分块)
                └── AgentKnowledgeQA ─── KnowledgeQA (向量化QA)

Conversation ─── Message
    │
    └── HumanSession ─── User (operator)
```

### 4.2 关键模型

**Agent**（`models/agent.py`）：

- 类型：orchestrator / faq / after-sale / custom
- 关联：模型配置、技能、工具、MCP 服务器、子 Agent、知识库文档、QA 对
- 配置：system_prompt、transfer_keywords（转人工关键词）、supported_channels（支持的渠道）

**Conversation**（`models/conversation.py`）：

- 状态：active → transferred → resolved / pending
- 渠道：web / feishu
- 处理者：agent / human

**ModelConfig**（`models/model_config.py`）：

- 多 LLM Provider 支持（base_url + api_key + model_id）
- API Key AES-GCM 加密存储
- 能力标记（capabilities JSONB）、上下文窗口大小

---

## 五、API 设计

统一 RESTful API（`/api/v1/`），采用 camelCase 响应格式：

```
认证模块    /api/v1/auth/*
仪表盘    /api/v1/dashboard/*
Agent管理  /api/v1/agents/*
工具管理    /api/v1/tools/*
技能管理    /api/v1/skills/*
知识库管理  /api/v1/knowledge/*
人工客服    /api/v1/human-service/*
历史记录    /api/v1/history/*
用户管理    /api/v1/users/*
系统设置    /api/v1/settings/*
API密钥    /api/v1/api-keys/*
聊天会话    /api/v1/chat/sessions/*
飞书Webhook /api/v1/feishu/*
WebSocket  /ws/admin, /ws/chat/{session_id}
```

统一响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

---

## 六、部署架构

Docker Compose 编排 7 个服务：

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| postgres | pgvector/pgvector:pg16 | 5432 | 主数据库 + 向量存储 |
| redis | redis:7-alpine | 6379 | 缓存 + 任务队列 |
| qdrant | qdrant/qdrant:latest | 6333 | 向量检索引擎 |
| neo4j | neo4j:5-community | 7687 | 知识图谱 |
| mongodb | mongo:7 | 27017 | 日志存储 |
| backend | 自建镜像 | 2811 | FastAPI 后端 |
| frontend | 自建镜像 | - | Next.js 前端 |
| gateway | nginx:alpine | 3534 | Nginx 反向代理 |

支持开发模式（`docker compose up`，自动加载 override.yml 挂载本地代码）和生产模式（`docker compose -f docker-compose.yml up`）。

---

## 七、项目亮点与技术难点

### 7.1 多 Agent 编排架构

采用 Orchestrator + Sub-Agent 模式，编排器通过 LLM Tool Calling 自主决策路由，支持最多 8 轮推理循环，子 Agent 结果回注上下文形成闭环。相比固定流程的 LangGraph 图，新 Runtime 更灵活，支持动态工具发现和并行工具调用。

### 7.2 多级降级的 RAG 系统

Qdrant → pgvector → ILIKE 三级降级策略，确保在任一组件故障时系统仍可提供基本的检索能力。QA 检索融合了语义相似度和关键词匹配的混合评分。

### 7.3 MCP 协议集成

完整实现 MCP (Model Context Protocol) 客户端，支持 SSE 和 stdio 两种传输模式，JSON-RPC 2.0 协议通信，实现外部工具的标准化接入。

### 7.4 多渠道统一接入

通过适配器模式抽象 IM 渠道差异，`IncomingMessage` 统一消息模型，新增渠道只需实现 `IMAdapter` 接口。已实现 Web 和飞书两个渠道。

### 7.5 Agent-知识库-图谱联动

Agent 配置自动同步到 Neo4j 知识图谱，可视化 Agent 之间的编排关系、知识依赖关系，支持基于图的查询分析。

### 7.6 安全设计

API Key 使用 AES-256-GCM 加密存储，JWT 双 Token 机制支持续期，请求限频和验证码防护，密码 bcrypt 哈希存储。

---

## 八、代码规模

| 维度 | 数据 |
|------|------|
| 后端 Python 文件 | 135 |
| 前端 TSX/TS 文件 | 51 |
| 后端类定义 | 225 |
| 后端函数/方法 | 792 |
| 后端接口定义 | 54 |
| Docker 服务数 | 7 |
| API 端点模块 | 13 |
| 数据库表 | ~15 |

---

## 📄 许可证

本项目采用 [GNU General Public License v3.0](LICENSE) 开源协议。