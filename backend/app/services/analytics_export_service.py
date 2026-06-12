"""
Analytics Export Service
数据分析导出服务：PostgreSQL 数据导出为 CSV
"""

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)


class AnalyticsExportService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _get_export_dir(self) -> Path:
        export_dir = Path(settings.snowflake_export_dir)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_dir = export_dir / date_str
        daily_dir.mkdir(parents=True, exist_ok=True)
        return daily_dir

    async def _export_table_to_csv(
        self,
        table_name: str,
        columns: list[str],
        order_by: str = "created_at",
    ) -> str:
        export_dir = self._get_export_dir()
        filepath = export_dir / f"{table_name}.csv"

        col_str = ", ".join(columns)
        query = text(f"SELECT {col_str} FROM {table_name} ORDER BY {order_by}")
        result = await self.db.execute(query)
        rows = result.fetchall()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([
                    val.isoformat() if isinstance(val, datetime) else val
                    for val in row
                ])

        logger.info("Exported %d rows to %s", len(rows), filepath)
        return str(filepath)

    async def export_conversations(self) -> str:
        return await self._export_table_to_csv(
            "conversations",
            [
                "id", "agent_id", "agent_name", "user_id", "user_name",
                "user_avatar", "session_id", "channel", "intent", "status",
                "handled_by", "resolution_note", "started_at", "ended_at",
                "created_at", "updated_at",
            ],
            order_by="started_at",
        )

    async def export_messages(self) -> str:
        return await self._export_table_to_csv(
            "messages",
            [
                "id", "conversation_id", "role", "content", "agent_name",
                "tool_calls", "created_at",
            ],
            order_by="created_at",
        )

    async def export_agent_usage(self) -> str:
        export_dir = self._get_export_dir()
        filepath = export_dir / "agent_usage.csv"

        query = text("""
            SELECT
                DATE(c.started_at) AS usage_date,
                c.agent_id,
                c.agent_name,
                a.type AS agent_type,
                COUNT(DISTINCT c.id) AS total_sessions,
                COUNT(DISTINCT CASE WHEN c.status = 'resolved' THEN c.id END) AS resolved_sessions,
                AVG(NULL) AS avg_response_ms
            FROM conversations c
            JOIN agents a ON c.agent_id = a.id
            GROUP BY DATE(c.started_at), c.agent_id, c.agent_name, a.type
            ORDER BY usage_date DESC
        """)
        result = await self.db.execute(query)
        rows = result.fetchall()

        columns = ["usage_date", "agent_id", "agent_name", "agent_type",
                   "total_sessions", "resolved_sessions", "avg_response_ms"]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([
                    row.usage_date.isoformat() if isinstance(row.usage_date, datetime) else row.usage_date,
                    row.agent_id,
                    row.agent_name,
                    row.agent_type,
                    row.total_sessions,
                    row.resolved_sessions,
                    row.avg_response_ms or 0,
                ])

        logger.info("Exported %d rows to %s", len(rows), filepath)
        return str(filepath)

    async def export_all(self) -> dict[str, str]:
        results = {}
        try:
            results["conversations"] = await self.export_conversations()
        except Exception:
            logger.warning("Failed to export conversations", exc_info=True)
            results["conversations"] = "error"
        try:
            results["messages"] = await self.export_messages()
        except Exception:
            logger.warning("Failed to export messages", exc_info=True)
            results["messages"] = "error"
        try:
            results["agent_usage"] = await self.export_agent_usage()
        except Exception:
            logger.warning("Failed to export agent_usage", exc_info=True)
            results["agent_usage"] = "error"
        return results