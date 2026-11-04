"""사이트마다 다른 크롤 결과를 하나의 모양으로 맞추는 공통 스키마.

사이트마다 목록 화면이 주는 정보가 다르다 (가격이 없는 곳, 날짜가 상대 시간인 곳 ...).
그래서 두 가지를 분리한다.

  SiteCapabilities : 그 사이트가 '원래' 주는 정보. 사이트마다 다르고 코드로 선언한다.
  NormalizedDeal   : 한 건의 정규화 결과. 값과 함께 '왜 이 값이 이런지'(status)를 가진다.

이렇게 하면 "가격이 비어 있다"가 세 가지로 구분된다.
    - 사이트가 가격을 주지 않는다 (capabilities.provides_price=False)  -> 정상
    - 줘야 하는데 안 왔다                                               -> 누락
    - 왔는데 읽지 못했다 (범위, 외화 ...)                               -> 파싱 실패
마크업이 바뀌어 파서가 조용히 망가지는 것(quality.py)은 뒤의 두 가지의 비율로 잡는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .price import PriceStatus


class FieldStatus(str, Enum):
    PARSED = "parsed"
    MISSING = "missing"  # 사이트가 주는 필드인데 이번 건에는 없음
    UNPARSEABLE = "unparseable"  # 값은 왔으나 읽지 못함
    NOT_PROVIDED = "not_provided_by_site"  # 이 사이트는 원래 이 정보를 주지 않음


@dataclass(frozen=True)
class SiteCapabilities:
    """사이트가 목록 화면에서 주는 정보와, 정상일 때 기대하는 채움 비율."""

    provides_price: bool
    provides_posted_at: bool
    search_supported: bool = False
    price_currency: str = "KRW"
    # 목록 한 번에서 가격/날짜가 읽혀야 하는 최소 비율. 이보다 낮으면 파서 이상을 의심한다.
    # 처음 값은 가정이다. 실제 서버에서 일주일쯤 수집한 뒤 실측 비율로 조정한다.
    expected_price_rate: float = 0.5
    expected_posted_at_rate: float = 0.5


@dataclass(frozen=True)
class NormalizedDeal:
    site_id: str
    title: str
    url: str
    price_krw: int | None
    price_status: PriceStatus
    price_field: FieldStatus
    price_raw: str | None
    posted_at: datetime | None  # UTC
    posted_at_field: FieldStatus
    posted_at_raw: str | None
    fetched_at: datetime
