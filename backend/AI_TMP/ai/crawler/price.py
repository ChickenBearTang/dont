"""가격 문자열 -> 원화 정수. 프로젝트의 단일 가격 파서.

예전 문제
    가격 파서가 xai/features.py 와 price_engine/normalizer.py 두 곳에 복사돼 있었고,
    둘 다 문자열 속 *모든* 숫자를 이어 붙였다.
        "5% 할인 21,200원"      -> 521200
        "10,000원 ~ 12,000원"   -> 1000012000
        "$12.99"                -> 1299
        "2개 39,000원"          -> 239000
        "21만원"                -> 21
    틀린 값이 조용히 가격 모델 학습 데이터와 실시간 구매 판단에 들어갔다.

원칙
    읽을 수 없으면 값을 만들지 않는다. 대신 왜 못 읽었는지를 status 로 남긴다.
    그래야 사이트 마크업이 바뀌어도(quality.py) 조용히 쓰레기가 쌓이지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata

# 이보다 큰 값은 파싱 오류로 본다 (1억 원).
MAX_PRICE_KRW = 100_000_000


class PriceStatus(str, Enum):
    PARSED = "parsed"
    FREE = "free"  # 무료 / 0원
    MISSING = "missing"  # 값 자체가 없음 (None, 빈 문자열, 문자열 아님)
    NO_NUMBER = "no_number"  # 문자열은 있으나 숫자가 없음 ("가격 미정")
    AMBIGUOUS = "ambiguous"  # 숫자가 여럿이라 하나로 정할 수 없음 (범위 등)
    FOREIGN_CURRENCY = "foreign_currency"  # 외화. 환율을 추측하지 않는다
    OUT_OF_RANGE = "out_of_range"


@dataclass(frozen=True)
class PriceParse:
    amount: int | None
    status: PriceStatus
    raw: str | None
    detail: str = ""

    @property
    def ok(self) -> bool:
        """금액을 얻었는가 (무료 포함)."""
        return self.amount is not None


_FOREIGN_MARKERS = re.compile(
    r"(\$|us\$|usd|달러|€|eur|유로|¥|jpy|엔|위안|cny|£|gbp|파운드)", re.IGNORECASE
)
_KRW_MARKERS = re.compile(r"(₩|원|krw)", re.IGNORECASE)
_FREE_MARKERS = re.compile(r"(무료|공짜|free)", re.IGNORECASE)

# 숫자 + 선택적 만/천 단위 + 선택적 원/KRW. 앞쪽 통화 기호(₩)는 별도로 본다.
_TOKEN = re.compile(
    r"(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>만|천)?\s*(?P<won>원|krw)?",
    re.IGNORECASE,
)
# 이 단위가 바로 뒤에 붙은 숫자는 가격이 아니다 (퍼센트, 수량, 기간 ...).
_NON_PRICE_SUFFIX = re.compile(r"^\s*(%|개|ea\b|배|일|시간|분|명|년)", re.IGNORECASE)
_UNIT_MULTIPLIER = {"만": 10_000, "천": 1_000}


def _to_number(text: str) -> float:
    return float(text.replace(",", ""))


def parse_price_krw(raw: object) -> PriceParse:
    if not isinstance(raw, str) or raw.strip() == "":
        return PriceParse(None, PriceStatus.MISSING, raw if isinstance(raw, str) else None, "no value")

    text = unicodedata.normalize("NFKC", raw).strip()  # ￦ -> ₩, 전각 쉼표 -> 쉼표
    has_krw_marker = _KRW_MARKERS.search(text) is not None
    has_digit = re.search(r"\d", text) is not None

    if not has_digit:
        if _FREE_MARKERS.search(text):
            return PriceParse(0, PriceStatus.FREE, raw, "free marker without amount")
        return PriceParse(None, PriceStatus.NO_NUMBER, raw, "no digits in text")

    if _FOREIGN_MARKERS.search(text) and not has_krw_marker:
        return PriceParse(None, PriceStatus.FOREIGN_CURRENCY, raw, "foreign currency marker")

    # 후보 수집. marked = 원화 표시(₩ 앞 / 원·KRW 뒤)가 붙은 금액.
    candidates: list[tuple[int, bool, bool]] = []  # (금액, marked, decimal 이었나)
    for match in _TOKEN.finditer(text):
        tail = text[match.end():]
        if match.group("unit") is None and match.group("won") is None and _NON_PRICE_SUFFIX.match(tail):
            continue
        number_text = match.group("num")
        value = _to_number(number_text)
        multiplier = _UNIT_MULTIPLIER.get(match.group("unit") or "", 1)
        amount = round(value * multiplier)
        preceded_by_won = text[: match.start()].rstrip().endswith("₩") or text[: match.start()].rstrip().lower().endswith("krw")
        marked = match.group("won") is not None or match.group("unit") is not None or preceded_by_won
        candidates.append((amount, marked, "." in number_text and match.group("unit") is None))

    # "2만 5천원" 처럼 단위가 이어지는 금액은 하나로 합친다.
    candidates = _merge_unit_runs(text, candidates)

    if not candidates:
        return PriceParse(None, PriceStatus.NO_NUMBER, raw, "digits found but none look like a price")

    pool = [c for c in candidates if c[1]] or candidates
    amounts = sorted({c[0] for c in pool})
    if len(amounts) > 1:
        return PriceParse(None, PriceStatus.AMBIGUOUS, raw, f"multiple amounts: {amounts}")

    amount, marked, was_decimal = pool[0]
    if was_decimal and not (marked or has_krw_marker):
        return PriceParse(None, PriceStatus.AMBIGUOUS, raw, "decimal amount without currency marker")
    if amount > MAX_PRICE_KRW:
        return PriceParse(None, PriceStatus.OUT_OF_RANGE, raw, f"{amount} exceeds {MAX_PRICE_KRW}")
    if amount == 0:
        return PriceParse(0, PriceStatus.FREE, raw, "zero amount")
    return PriceParse(amount, PriceStatus.PARSED, raw)


_RUN = re.compile(
    r"(?P<a>\d[\d,]*(?:\.\d+)?)\s*만\s*(?P<b>\d[\d,]*)\s*천\s*(?P<won>원|krw)?",
    re.IGNORECASE,
)


def _merge_unit_runs(text: str, candidates: list[tuple[int, bool, bool]]) -> list[tuple[int, bool, bool]]:
    """'2만 5천원' -> 25000. 개별 토큰(20000, 5000)을 합친 한 금액으로 바꾼다."""
    run = _RUN.search(text)
    if run is None:
        return candidates
    merged = round(_to_number(run.group("a")) * 10_000 + _to_number(run.group("b")) * 1_000)
    return [(merged, True, False)]
