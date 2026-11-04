"""게시 시각 문자열 -> UTC datetime.

목록 화면은 연도를 생략하거나(12-31), 오늘 글은 시각만(13:45) 보여준다.
이 사이트들은 한국 시간(KST)이므로 KST 로 해석해서 UTC 로 바꾼다.
읽을 수 없으면 값을 만들지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
import unicodedata

from .schema import FieldStatus

KST = timezone(timedelta(hours=9))

_FULL_DATE = re.compile(r"^(\d{4})[./-](\d{1,2})[./-](\d{1,2})$")
_MONTH_DAY = re.compile(r"^(\d{1,2})[./-](\d{1,2})$")
_TIME_ONLY = re.compile(r"^(\d{1,2}):(\d{2})$")


@dataclass(frozen=True)
class PostedAtParse:
    value: datetime | None
    field: FieldStatus
    raw: str | None


def parse_posted_at(raw: object, *, now: datetime) -> PostedAtParse:
    """now 는 timezone-aware 여야 한다 (수집 시각)."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if not isinstance(raw, str) or raw.strip() == "":
        return PostedAtParse(None, FieldStatus.MISSING, raw if isinstance(raw, str) else None)

    text = unicodedata.normalize("NFKC", raw).strip()
    now_kst = now.astimezone(KST)

    try:
        match = _FULL_DATE.match(text)
        if match:
            local = datetime(int(match[1]), int(match[2]), int(match[3]), tzinfo=KST)
            return PostedAtParse(local.astimezone(timezone.utc), FieldStatus.PARSED, raw)

        match = _MONTH_DAY.match(text)
        if match:
            local = datetime(now_kst.year, int(match[1]), int(match[2]), tzinfo=KST)
            if local > now_kst + timedelta(days=1):  # 미래 날짜 = 작년 글
                local = local.replace(year=now_kst.year - 1)
            return PostedAtParse(local.astimezone(timezone.utc), FieldStatus.PARSED, raw)

        match = _TIME_ONLY.match(text)
        if match:
            local = now_kst.replace(hour=int(match[1]), minute=int(match[2]), second=0, microsecond=0)
            if local > now_kst:  # 시각만 보이는 글은 24시간 이내. 미래면 어제 글
                local -= timedelta(days=1)
            return PostedAtParse(local.astimezone(timezone.utc), FieldStatus.PARSED, raw)
    except ValueError:  # 13월, 32일, 25:00 같은 값
        return PostedAtParse(None, FieldStatus.UNPARSEABLE, raw)

    return PostedAtParse(None, FieldStatus.UNPARSEABLE, raw)
