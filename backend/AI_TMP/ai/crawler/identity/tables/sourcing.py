"""제목/주소에서 유통경로(정식수입 · 병행수입 · 직구 · 구매대행)를 알아낸다.

경로가 중요한 이유: 같은 상품이어도 직구/병행수입은 관부가세, 배송, 보증이 달라 가격 수준이 다르다.
섞어서 가격 이력을 쌓으면 '싼 가격'이 사실은 다른 경로의 가격이다. sourcing_categories 의 price_pool_yn
이 N 이면 경로별로 따로 쌓는다. kc_record_expected_yn 이 Y 인데 카탈로그에 기록이 없으면 카탈로그 공백이라
알려 주고, N 이면(직구 등) 기록이 없는 것이 정상이다.

판정 규칙 (추측하지 않는다)
  1. 켜진 신호만 쓴다. 신호는 keyword(공백/기호 무시 포함), token(토큰 일치), domain(주소 호스트).
  2. 일치한 신호 중 priority 숫자가 가장 작은 것들만 본다.
  3. 그것들이 한 경로를 가리키면 그 경로, 서로 다른 경로면 'conflict' 로 알리고 고르지 않는다.
  4. 신호가 없으면 'none'. 경로를 모른다고 국내 판매로 가정하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable
from urllib.parse import urlsplit

from ..text import compact, tokenize
from .models import Issue, ProductTables, SourcingCategoryRow, SourcingSignalRow
from .validate import clean_sourcing


@dataclass(frozen=True)
class SourcingResult:
    status: str  # "classified" | "conflict" | "none"
    category_code: str | None = None
    label_ko: str | None = None
    kc_record_expected: str | None = None  # 'Y' | 'N' | 'U'
    price_pool: bool | None = None  # False 면 이 경로의 가격은 다른 경로와 합치지 않는다
    reviewed: bool | None = None  # 이 경로의 Y/N 값을 사람이 확인했는가
    evidence: tuple[str, ...] = ()
    conflicting: tuple[str, ...] = ()  # conflict 일 때 서로 다툰 경로


NONE = SourcingResult("none")


_BARE_HOST = re.compile(r"^[a-z0-9][a-z0-9.\-]*(:\d{1,5})?([/?#].*)?$", re.IGNORECASE)


def host_of(url: str | None) -> str | None:
    """주소에서 호스트를 뽑는다. 스킴이 없어도 호스트 모양(aliexpress.com/item/1)이면 받고,
    javascript:, mailto:, ftp: 같은 것은 주소로 보지 않는다."""
    if not url or not isinstance(url, str):
        return None
    text = url.strip()
    if not text:
        return None
    if "//" not in text:
        if not _BARE_HOST.match(text):
            return None
        text = "//" + text
    try:
        parts = urlsplit(text)
    except ValueError:
        return None
    if parts.scheme not in ("", "http", "https"):
        return None
    host = (parts.hostname or "").lower().strip(".")
    return host or None


@dataclass(frozen=True)
class _Signal:
    row: SourcingSignalRow
    tokens: tuple[str, ...]  # keyword/token 용
    needle: str  # keyword: 공백 없이 이은 값 / domain: 호스트


class SourcingClassifier:
    def __init__(self, categories: Iterable[SourcingCategoryRow], signals: Iterable[SourcingSignalRow]) -> None:
        self.issues: list[Issue] = []
        self._categories = {c.category_code: c for c in categories}
        self._signals: list[_Signal] = []
        for row in signals:
            if row.enabled_yn != "Y" or row.category_code not in self._categories:
                continue
            norm = row.pattern_norm
            self._signals.append(_Signal(row, tuple(norm.split()) if row.match_type != "domain" else (), norm.replace(" ", "")))

    @classmethod
    def from_tables(cls, tables: ProductTables) -> "SourcingClassifier":
        """검증을 통과한 행만 쓴다. 걸러진 행은 classifier.issues 에 남는다."""
        categories, signals, issues = clean_sourcing(tables.categories, tables.signals)
        classifier = cls(categories, signals)
        classifier.issues = issues
        return classifier

    def __len__(self) -> int:
        return len(self._signals)

    def category(self, code: str | None) -> SourcingCategoryRow | None:
        return self._categories.get(code) if code else None

    def classify(self, title: str, url: str | None = None) -> SourcingResult:
        tokens = tokenize(title or "")
        joined = compact(tokens)[0]
        host = host_of(url)
        hits: list[tuple[int, _Signal]] = []
        for signal in self._signals:
            kind = signal.row.match_type
            if kind == "keyword":
                matched = signal.needle in joined
            elif kind == "token":
                n = len(signal.tokens)
                matched = n > 0 and any(tuple(tokens[i:i + n]) == signal.tokens for i in range(len(tokens) - n + 1))
            else:  # domain
                matched = host is not None and (host == signal.needle or host.endswith("." + signal.needle))
            if matched:
                hits.append((signal.row.priority, signal))
        if not hits:
            return NONE
        best = min(priority for priority, _ in hits)
        decisive = [s for priority, s in hits if priority == best]
        evidence = tuple(f"{s.row.match_type} '{s.row.pattern}' -> {s.row.category_code}" for s in decisive)
        codes = sorted({s.row.category_code for s in decisive})
        if len(codes) > 1:
            return SourcingResult("conflict", evidence=evidence, conflicting=tuple(codes))
        category = self._categories[codes[0]]
        return SourcingResult(
            "classified", category.category_code, category.label_ko, category.kc_record_expected_yn,
            category.price_pool_yn == "Y", category.reviewed_yn == "Y", evidence,
        )
