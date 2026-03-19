from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HotDeal:
    title: str
    url: str
    price: str | None = None


@dataclass(frozen=True)
class CrawlResult:
    source: str
    fetched_at: datetime
    items: list[HotDeal]
