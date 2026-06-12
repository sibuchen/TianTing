"""
Application Configuration
环境变量配置管理
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=["../.env", ".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "TianTing"
    app_version: str = "1.0.0"
    app_port: int = 2811
    debug: bool = False
    environment: Literal["development", "production", "testing"] = "development"

    # API
    api_v1_prefix: str = "/api/v1"
    openapi_url: str | None = "/openapi.json"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    # CORS
    cors_origins: list[str] = ["http://localhost:2424"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://sibuchen:postgres-sibuchen-password@localhost:5432/tianting"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False

    # Redis
    redis_url: str = Field(default="redis://:redis-sibuchen-password@localhost:6379/0")
    redis_max_connections: int = 50

    # JWT
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours
    jwt_refresh_token_expire_days: int = 7
    jwt_access_token_expire_days_remember: int = 30
    jwt_refresh_token_expire_days_remember: int = 30

    # Security
    password_min_length: int = 8
    bcrypt_rounds: int = 12

    # Encryption (for API Keys)
    encryption_key: str = Field(default="your-32-byte-encryption-key!")

    # Token Store
    token_store_dir: str = Field(default="")

    # Tianting Home
    tianting_home: str = Field(default="", alias="TIANTING_HOME")

    # File Upload
    upload_dir: str = "/tmp/tianting/uploads"
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: list[str] = ["pdf", "docx", "txt", "md"]

    # Rate Limiting
    rate_limit_per_minute: int = 60
    chat_rate_limit_per_minute: int = 30

    # Cache TTL
    cache_ttl_conversation: int = 300
    cache_ttl_chat_history: int = 600
    cache_ttl_agent_config: int = 1800
    cache_chat_history_max_len: int = 50

    # ARQ Redis
    arq_redis_url: str = Field(default="redis://:redis-sibuchen-password@localhost:6379/1")

    # LangGraph Checkpoint
    langgraph_checkpointer: Literal["postgres"] = "postgres"

    # RAG
    embed_model_base_url: str | None = Field(default="https://integrate.api.nvidia.com/v1", alias="EMBED_MODEL_BASE_URL")
    embed_model_api_key: str | None = Field(default="nvapi-sibuchen-free-api-key", alias="EMBED_MODEL_API_KEY")
    embed_model_id: str | None = Field(default="nvidia/nv-embed-v1", alias="EMBED_MODEL_ID")
    embed_model_dimension: int | None = Field(default=4096, alias="EMBED_MODEL_DIMENSION")
    embedding_model: str = "nvidia/nv-embed-v1"
    embedding_dimension: int = 4096
    chunk_size: int = 500
    chunk_overlap: int = 50
    retrieval_top_k: int = 5

    # Qdrant
    qdrant_enabled: bool = False
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str | None = Field(default="qdrant-sibuchen-password")
    qdrant_collection_prefix: str = "tianting"

    # LLM Default
    default_model_config_id: str | None = None

    # Feishu IM
    feishu_enabled: bool = False
    feishu_app_id: str = Field(default="")
    feishu_app_secret: str = Field(default="")
    feishu_verification_token: str = Field(default="")
    feishu_encrypt_key: str = Field(default="")
    feishu_event_mode: Literal["webhook", "websocket"] = "websocket"

    # Neo4j
    neo4j_enabled: bool = False
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="neo4j-sibuchen-password")

    # MongoDB
    mongodb_enabled: bool = False
    mongodb_url: str = Field(default="mongodb://sibuchen:mongo-sibuchen-password@localhost:27017/tianting?authSource=admin")
    mongodb_db_name: str = "tianting"

    # Snowflake
    snowflake_enabled: bool = False
    snowflake_export_dir: str = "./data/exports"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
