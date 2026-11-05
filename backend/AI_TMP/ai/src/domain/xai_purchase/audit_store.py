from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any

from config import RUNTIME_DIR


class JsonlXaiAuditLogStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (RUNTIME_DIR / "xai_audit_log.jsonl")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # 사용자 반응이 '우리가 만든 평가'에 대한 것인지 확인하는 색인.
        # 파일은 추가만 되므로 지난번에 읽은 곳부터 새로 생긴 줄만 읽는다.
        self._known: dict[str, int] = {}
        self._read_offset = 0
        self._index_lock = threading.Lock()

    def purchase_request_id_for(self, request_id: str) -> int | None:
        """이 requestId 로 평가한 기록이 있으면 그 purchaseRequestId, 없으면 None."""
        with self._index_lock:
            if not self._path.exists():
                return None
            if self._path.stat().st_size < self._read_offset:
                # 파일이 잘렸거나 교체됐다. 색인을 처음부터 다시 만든다.
                self._known.clear()
                self._read_offset = 0
            with self._path.open("rb") as handle:
                handle.seek(self._read_offset)
                chunk = handle.read()
            # 쓰는 도중인 마지막 줄은 개행이 올 때까지 읽지 않는다.
            end = chunk.rfind(b"\n") + 1
            for raw_line in chunk[:end].splitlines():
                try:
                    row = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue
                rid, pid = row.get("requestId"), row.get("purchaseRequestId")
                if isinstance(rid, str) and isinstance(pid, int) and not isinstance(pid, bool):
                    self._known.setdefault(rid, pid)
            self._read_offset += end
            return self._known.get(request_id)

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
