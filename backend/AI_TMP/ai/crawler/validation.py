"""크롤 결과 한 건의 오염 검증.

수집 단계에서 오염된 값은 가격 이력과 모델 학습을 통째로 오염시킨다 (예전에 가격 파서가
'5% 할인 21,200원' 을 521200 으로 읽은 것처럼). 의심스러운 값은 코드와 함께 남기고,
쓸 수 없는 값(오류)은 격리한다.

    오류(error)  : 이 글은 저장/학습에 쓰지 않는다 (URL 이 깨짐, 제목이 비었음, 미래 날짜, 가격 상한 초과)
    경고(warning): 쓸 수는 있으나 값을 의심한다 (범위/외화 가격, 의심스럽게 작은 가격, 제목-가격 불일치)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import re
import unicodedata
from urllib.parse import urlparse

from .price import PriceStatus
from .schema import NormalizedDeal

LOW_PRICE_KRW = 1_000
TITLE_PRICE_TOLERANCE = 0.01  # 제목의 가격과 가격란이 1% 넘게 다르면 의심
MAX_AGE = timedelta(days=365 * 3)
FUTURE_SLACK = timedelta(days=1)  # 시간대/표기 오차

_KRW_IN_TITLE = re.compile(r"(\d[\d,]*)\s*원")


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class DealIssue:
    code: str
    severity: Severity
    message: str


def validate_deal(deal: NormalizedDeal, *, now: datetime) -> list[DealIssue]:
    issues: list[DealIssue] = []
    err, warn = Severity.ERROR, Severity.WARNING

    title = deal.title.strip()
    if title == "":
        issues.append(DealIssue("TITLE_EMPTY", err, "제목이 비었다"))
    elif len(title) < 2:
        issues.append(DealIssue("TITLE_TOO_SHORT", warn, "제목이 너무 짧다"))
    elif title.replace(",", "").isdigit():
        issues.append(DealIssue("TITLE_ONLY_DIGITS", warn, "제목이 숫자뿐이다"))

    parsed = urlparse(deal.url or "")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        issues.append(DealIssue("URL_INVALID", err, "URL 이 http(s) 주소가 아니거나 호스트가 없다"))

    status = deal.price_status
    if status == PriceStatus.OUT_OF_RANGE:
        issues.append(DealIssue("PRICE_OUT_OF_RANGE", err, "가격이 상한을 넘는다 (파싱 오류로 의심)"))
    elif status == PriceStatus.AMBIGUOUS:
        issues.append(DealIssue("PRICE_AMBIGUOUS", warn, "가격이 범위/여러 금액이라 하나로 정할 수 없다"))
    elif status == PriceStatus.FOREIGN_CURRENCY:
        issues.append(DealIssue("PRICE_FOREIGN_CURRENCY", warn, "외화 가격이라 원화로 바꾸지 않았다"))
    if deal.price_krw is not None:
        if deal.price_krw == 0:
            issues.append(DealIssue("PRICE_ZERO", warn, "가격이 0원/무료다 (사은품 글이거나 파싱 오류)"))
        elif deal.price_krw < LOW_PRICE_KRW:
            issues.append(DealIssue("PRICE_SUSPICIOUSLY_LOW", warn, f"가격이 {LOW_PRICE_KRW:,}원 미만이라 파싱 오류일 수 있다"))
        amounts = {int(m.replace(",", "")) for m in _KRW_IN_TITLE.findall(unicodedata.normalize("NFKC", deal.title))}
        if len(amounts) == 1:
            (in_title,) = amounts
            if in_title > 0 and abs(in_title - deal.price_krw) / in_title > TITLE_PRICE_TOLERANCE:
                issues.append(DealIssue(
                    "PRICE_TITLE_MISMATCH", warn,
                    f"제목의 가격({in_title:,}원)과 가격란({deal.price_krw:,}원)이 다르다 (어느 한쪽 파싱 오류 의심)",
                ))

    if deal.posted_at is not None:
        if deal.posted_at > now + FUTURE_SLACK:
            issues.append(DealIssue("POSTED_AT_FUTURE", err, "게시 시각이 미래다"))
        elif now - deal.posted_at > MAX_AGE:
            issues.append(DealIssue("POSTED_AT_TOO_OLD", warn, "게시 시각이 3년보다 오래됐다"))
    return issues
