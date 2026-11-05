"""사용자 반응 저장소 (추가 전용 JSONL).

같은 (평가 requestId, 대상 aspect) 에 여러 번 들어와도 지우지 않고 모두 남긴다.
'현재 값'은 가장 나중 기록이다. 재전송(같은 값)은 다시 쓰지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading
from typing import Any, Iterator

from config import RUNTIME_DIR

from .schemas import FeedbackStatus, PurchaseFeedbackRequest


@dataclass(frozen=True)
class StoredFeedback:
    feedback_id: str
    status: FeedbackStatus


def feedback_id_for(request_id: str, aspect: str, verdict: str, action: str, reasons: list[str]) -> str:
    """내용이 같으면 같은 id. 재전송을 중복으로 알아보는 데 쓴다."""
    raw = json.dumps([request_id, aspect, verdict, action, sorted(reasons)], ensure_ascii=False)
    return "fb_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


class JsonlFeedbackStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (RUNTIME_DIR / "xai_feedback.jsonl")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        # (requestId, aspect) -> 현재 값의 feedbackId. 시작할 때 파일에서 복원한다.
        self._current: dict[tuple[str, str], str] = {}
        for row in self.iter_rows():
            self._current[(row["requestId"], row["aspect"])] = row["feedbackId"]

    def iter_rows(self) -> Iterator[dict[str, Any]]:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue  # 잘린 줄 하나가 전체 읽기를 막지 않게 한다
                if isinstance(row, dict) and {"requestId", "aspect", "feedbackId"} <= row.keys():
                    yield row

    def save(self, request_id: str, body: PurchaseFeedbackRequest) -> StoredFeedback:
        reasons = [reason.value for reason in body.reasons]
        feedback_id = feedback_id_for(
            request_id, body.aspect.value, body.verdict.value, body.action.value, reasons
        )
        key = (request_id, body.aspect.value)
        with self._lock:
            previous = self._current.get(key)
            if previous == feedback_id:
                return StoredFeedback(feedback_id, FeedbackStatus.DUPLICATE)
            row = {
                "feedbackId": feedback_id,
                "requestId": request_id,
                "purchaseRequestId": body.purchase_request_id,
                "aspect": body.aspect.value,
                "verdict": body.verdict.value,
                "action": body.action.value,
                "reasons": reasons,
                "comment": body.comment,
                "clientSubmittedAt": body.client_submitted_at.isoformat() if body.client_submitted_at else None,
                "receivedAt": datetime.now(timezone.utc).isoformat(),
                "supersedes": previous,
            }
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            self._current[key] = feedback_id
            status = FeedbackStatus.RECORDED if previous is None else FeedbackStatus.CHANGED
            return StoredFeedback(feedback_id, status)

    def current_rows(self) -> list[dict[str, Any]]:
        """(requestId, aspect) 마다 마지막 기록만. 내보내기/집계는 이것을 쓴다."""
        latest: dict[tuple[str, str], dict[str, Any]] = {}
        for row in self.iter_rows():
            latest[(row["requestId"], row["aspect"])] = row
        return list(latest.values())
