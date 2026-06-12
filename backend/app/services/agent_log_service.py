import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.mongo_log_service import mongo_log_service


class AgentLogService:
    def __init__(self):
        self._log_dir = self._resolve_log_dir()

    def _resolve_log_dir(self) -> Path:
        tianting_home = settings.tianting_home
        if tianting_home:
            base = Path(tianting_home)
        else:
            base = Path.home()
        return base / ".tianting" / "agent_logs"

    def _ensure_dir(self, conversation_id: str) -> Path:
        now = datetime.now(timezone.utc)
        date_dir = self._log_dir / now.strftime("%Y-%m-%d") / conversation_id
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir

    def _get_next_sequence(self, dir_path: Path) -> int:
        existing = list(dir_path.glob("*.json"))
        return len(existing) + 1

    async def write_log(
        self,
        conversation_id: str,
        agent_id: str,
        agent_name: str,
        operation_type: str,
        operation_detail: dict[str, Any],
        parent_log_id: str | None = None,
        duration_ms: int | None = None,
    ) -> str:
        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        dir_path = self._ensure_dir(conversation_id)
        seq = self._get_next_sequence(dir_path)

        timestamp_str = now.strftime("%H%M%S%f")
        agent_id_short = agent_id[:8] if agent_id else "unknown"
        filename = f"{seq:04d}_{operation_type}_{agent_id_short}_{timestamp_str}.json"
        filepath = dir_path / filename

        log_entry = {
            "id": log_id,
            "conversation_id": conversation_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "operation_type": operation_type,
            "operation_detail": operation_detail,
            "parent_log_id": parent_log_id,
            "duration_ms": duration_ms,
            "created_at": now.isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False, indent=2)

        try:
            await mongo_log_service.write_operation_log(
                log_id=log_id,
                conversation_id=conversation_id,
                agent_id=agent_id,
                agent_name=agent_name,
                operation_type=operation_type,
                operation_detail=operation_detail,
                parent_log_id=parent_log_id,
                duration_ms=duration_ms,
            )
        except Exception:
            pass

        return log_id

    async def query_logs(
        self,
        conversation_id: str,
        date: str | None = None,
    ) -> list[dict[str, Any]]:
        mongo_logs = await mongo_log_service.query_operation_logs(conversation_id)
        if mongo_logs:
            return mongo_logs

        logs = []

        if date:
            search_dirs = [self._log_dir / date / conversation_id]
        else:
            search_dirs = []
            if self._log_dir.exists():
                for date_dir in sorted(self._log_dir.iterdir()):
                    if date_dir.is_dir():
                        conv_dir = date_dir / conversation_id
                        if conv_dir.exists():
                            search_dirs.append(conv_dir)

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for json_file in sorted(search_dir.glob("*.json")):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        log_entry = json.load(f)
                        logs.append(log_entry)
                except Exception:
                    pass

        return logs


agent_log_service = AgentLogService()
