# TianTing 天听智能客服系统

天听智能客服系统后端服务，基于 FastAPI 构建，提供完整的智能客服功能。

## 功能特性

- 🤖 **多Agent编排**: 基于 LangGraph 的智能客服编排引擎
- 📚 **RAG知识库**: 支持文档上传、分块、向量化检索
- 🔧 **MCP集成**: 支持 MCP Server 连接与工具调用
- 💬 **实时对话**: 支持 WebSocket 和 SSE 流式响应
- 👥 **人工客服**: 完整的人工客服工作流
- 📊 **数据分析**: 实时仪表盘与对话统计

## 技术栈

- **Web框架**: FastAPI 0.115+
- **数据库**: PostgreSQL 16 + pgvector
- **缓存**: Redis 7.0+
- **Agent编排**: LangGraph 0.2+
- **异步任务**: ARQ

## 快速开始

### 方式一: Docker Compose (推荐)

```bash
# 克隆项目
git clone <repository_url>
cd backend

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 方式二: 本地开发

#### 前置条件

- Python 3.12+
- PostgreSQL 16+ (启用 pgvector 扩展)
- Redis 7.0+

#### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和 Redis 连接
```

#### 初始化数据库

```bash
# 连接 PostgreSQL 并创建扩展
psql -U sibuchen -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 执行初始化脚本
psql -U sibuchen -d tianting -f ../init.sql
```

#### 启动服务

```bash
# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动 ARQ Worker (另一个终端)
arq app.tasks.worker:WorkerSettings
```

## API文档

启动服务后访问:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 项目结构

```
backend/
├── app/
│   ├── api/              # API路由层
│   │   ├── admin/        # 管理后台API
│   │   └── chat/         # 聊天窗口API
│   ├── models/           # SQLAlchemy ORM模型
│   ├── schemas/          # Pydantic数据模型
│   ├── services/         # 业务逻辑层
│   ├── agents/           # LangGraph Agent实现
│   │   ├── nodes/        # Agent节点
│   │   └── tools/        # 内置工具
│   ├── rag/              # RAG引擎
│   ├── tasks/            # ARQ异步任务
│   ├── core/             # 核心基础设施
│   └── ws/               # WebSocket管理

├── docker/               # Docker配置
└── tests/                # 测试目录
```

## API接口

### 认证模块
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/refresh` - 刷新Token
- `POST /api/v1/auth/logout` - 用户登出

### 仪表盘
- `GET /api/v1/dashboard/metrics` - 核心指标
- `GET /api/v1/dashboard/realtime-status` - 实时状态
- `GET /api/v1/dashboard/intent-distribution` - 意图分布

### Agent管理
- `GET /api/v1/agents` - 获取Agent列表
- `POST /api/v1/agents` - 创建Agent
- `GET /api/v1/agents/:id` - Agent详情
- `PUT /api/v1/agents/:id` - 更新Agent
- `PATCH /api/v1/agents/:id/toggle` - 启用/禁用

### 知识库管理
- `GET /api/v1/knowledge/documents` - 文档列表
- `POST /api/v1/knowledge/documents/upload` - 上传文档
- `GET /api/v1/knowledge/qa` - Q&A列表
- `POST /api/v1/knowledge/qa` - 创建Q&A

### 聊天窗口API
- `POST /api/v1/chat/sessions` - 创建会话
- `GET /api/v1/chat/sessions/:id/messages` - 消息历史
- `POST /api/v1/chat/sessions/:id/messages` - 发送消息

### WebSocket
- `WS /ws/admin` - Admin实时通信
- `WS /ws/chat/:session_id` - 聊天实时通信

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | PostgreSQL连接URL | postgresql+asyncpg://... |
| REDIS_URL | Redis连接URL | redis://localhost:6379/0 |
| JWT_SECRET_KEY | JWT密钥 | - |
| ENCRYPTION_KEY | API Key加密密钥 (32字节) | - |

### 数据库

数据库表结构请参考 `init.sql` 文件。

## 开发指南

### 代码规范

```bash
# 代码检查
ruff check .

# 代码格式化
ruff format .

# 类型检查
mypy app/
```

### 测试

```bash
# 运行测试
pytest

# 带覆盖率
pytest --cov=app tests/
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t tianting-backend .

# 运行容器
docker run -d -p 8000:8000 --env-file .env tianting-backend
```

### 生产环境

建议使用:
- Nginx 作为反向代理
- Gunicorn + Uvicorn workers
- Supervisor 管理进程
- PM2 管理 Node.js (如有前端)

## 许可证

MIT License
