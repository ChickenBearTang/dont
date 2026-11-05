"""수집 품질 점검: 사이트 마크업이 바뀌어 파서가 조용히 망가지는 것을 잡는다.

정규식 파서는 마크업이 바뀌면 에러 없이 0건이나 빈 필드를 돌려준다. 하루 300건씩
서버에서 계속 돌리는 크롤러가 쓰레기를 쌓아도 아무도 모르게 된다. 한 번의 수집
결과에서 아래를 점검해 이상이면 알린다.

  EMPTY_RESULT          : 0건. 마크업이 바뀌었거나 차단됐을 가능성
  LOW_PRICE_RATE        : 사이트가 가격을 주는데 읽힌 비율이 기대보다 낮음
  LOW_POSTED_AT_RATE    : 날짜도 같음
  DUPLICATE_URLS        : 같은 URL 이 한 번에 여러 번
  EMPTY_TITLES          : 제목이 빈 건
사이트가 원래 주지 않는 필드(NOT_PROVIDED)는 점검하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .schema import FieldStatus, NormalizedDeal, SiteCapabilities


@dataclass(frozen=True)
class QualityReport:
    ok: bool
    issues: list[str]
    stats: dict[str, float | int] = field(default_factory=dict)


def assess_batch(
    deals: Sequence[NormalizedDeal],
    capabilities: SiteCapabilities,
    *,
    min_items_for_rates: int = 5,
) -> QualityReport:
    total = len(deals)
    issues: list[str] = []
    stats: dict[str, float | int] = {"items": total}

    if total == 0:
        return QualityReport(False, ["EMPTY_RESULT"], stats)

    empty_titles = sum(1 for d in deals if d.title.strip() == "")
    if empty_titles:
        issues.append("EMPTY_TITLES")
    stats["empty_titles"] = empty_titles

    unique_urls = len({d.url for d in deals})
    if unique_urls < total:
        issues.append("DUPLICATE_URLS")
    stats["duplicate_urls"] = total - unique_urls

    # 건수가 너무 적으면 비율이 의미 없다 (한두 건의 우연한 누락).
    if total >= min_items_for_rates:
        if capabilities.provides_price:
            rate = sum(1 for d in deals if d.price_field == FieldStatus.PARSED) / total
            stats["price_parsed_rate"] = round(rate, 4)
            if rate < capabilities.expected_price_rate:
                issues.append("LOW_PRICE_RATE")
        if capabilities.provides_posted_at:
            rate = sum(1 for d in deals if d.posted_at_field == FieldStatus.PARSED) / total
            stats["posted_at_parsed_rate"] = round(rate, 4)
            if rate < capabilities.expected_posted_at_rate:
                issues.append("LOW_POSTED_AT_RATE")

    return QualityReport(not issues, issues, stats)
