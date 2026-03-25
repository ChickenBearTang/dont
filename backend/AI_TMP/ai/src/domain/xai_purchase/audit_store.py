from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from config import DATA_DIR


class JsonlXaiAuditLogStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (DATA_DIR / "xai_audit_log.jsonl")
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        *,
        request_id: str,
        purchase_request_id: int,
        warnings: list[str],
        runtime_engines: dict[str, Any],
        audit_logs: list[dict[str, Any]],
    ) -> None:
        logged_at = datetime.now(timezone.utc).isoformat()
        rows = audit_logs or [{}]
        with self._path.open("a", encoding="utf-8") as handle:
            for row in rows:
                payload = {
                    "requestId": request_id,
                    "purchaseRequestId": purchase_request_id,
                    "loggedAt": logged_at,
                    "warnings": warnings,
                    "runtimeEngines": runtime_engines,
                    **row,
                }
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
