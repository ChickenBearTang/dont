from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..models import CrawlResult
from ..models import HotDeal


@dataclass(frozen=True)
class SaveStats:
    inserted: int
    updated: int


class CrawlStore(Protocol):
    def is_seen(self, deal: HotDeal) -> bool: ...

    def save_result(self, result: CrawlResult) -> SaveStats: ...
