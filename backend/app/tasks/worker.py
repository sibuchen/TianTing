"""
ARQ Worker
ARQ Worker启动配置
"""

from arq import cron
from arq.connections import RedisSettings

from app.tasks.document_tasks import process_document_vectorization


async def startup(ctx: dict) -> None:
    """Worker启动"""
    pass


async def shutdown(ctx: dict) -> None:
    """Worker关闭"""
    pass


class WorkerSettings:
    """Worker配置"""

    redis_settings = RedisSettings.from_dsn("redis://localhost:6379/1")

    functions = [
        process_document_vectorization,
    ]

    cron_jobs = [
        cron(process_document_vectorization, hour=2, minute=0),
    ]

    on_startup = startup
    on_shutdown = shutdown


def get_worker() -> WorkerSettings:
    """获取Worker配置"""
    return WorkerSettings
