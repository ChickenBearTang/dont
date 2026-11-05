"""테이블 한 줄에 해당하는 값 객체와 허용 값.

DB 테이블(sql/product_tables_v1.sql)과 CSV 파일(data/tables/*.csv)은 같은 열을 쓰고, 이 모듈의
dataclass 가 둘 사이의 공통 표현이다. 여기서는 형식만 정한다. 값이 맞는지(충돌, 고아 행 ...)는
validate.py 가 본다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..text import compact_code, tokenize

YN = ("Y", "N")
YNU = ("Y", "N", "U")

CATALOG_SOURCES = ("kc", "curated", "seed", "import_only")
ALIAS_KINDS = ("model", "line")
ALIAS_TYPES = (
    "marketing", "korean", "english", "abbreviation", "colloquial", "misspelling", "kc_derived", "part_number", "other",
)
ALIAS_STATUSES = ("approved", "pending", "rejected")
ALIAS_SOURCES = ("curated", "kc", "crawl_suggested", "llm_suggested", "user_report")
MATCH_TYPES = ("keyword", "token", "domain")

# 인증 DB 기준 항목이 아닌 상품도 담을 수 있다. 직구로만 들어오는 상품은 kc_certified_yn='N', source='import_only'.
KC_CERTIFIED_MEANING = {"Y": "인증 DB 기록 있음", "N": "인증 DB 기록 없음", "U": "확인 안 함"}


@dataclass(frozen=True)
class CatalogRow:
    catalog_id: str
    brand: str
    model_code: str
    display_name: str | None = None
    product_line: str = ""
    category: str = ""
    manufacturer: str | None = None
    kc_certified_yn: str = "U"
    kc_info: dict[str, Any] = field(default_factory=dict)
    source: str = "curated"
    verified_yn: str = "N"
    requires_brand_yn: str = "N"
    compatible_brands: tuple[str, ...] = ()
    benign_suffixes: tuple[str, ...] = ()

    @property
    def model_code_norm(self) -> str:
        return compact_code(self.model_code)


@dataclass(frozen=True)
class AliasRow:
    catalog_id: str
    alias_text: str
    alias_kind: str = "model"
    alias_type: str = "other"
    brand_required_yn: str = "N"
    status: str = "pending"
    source: str = "curated"
    note: str | None = None
    reviewed_by: str | None = None

    @property
    def alias_norm(self) -> str:
        return compact_code(self.alias_text)


@dataclass(frozen=True)
class SourcingCategoryRow:
    category_code: str
    label_ko: str
    kc_record_expected_yn: str
    price_pool_yn: str
    reviewed_yn: str = "N"
    sort_order: int = 100
    note: str | None = None


@dataclass(frozen=True)
class SourcingSignalRow:
    category_code: str
    match_type: str
    pattern: str
    priority: int = 100
    enabled_yn: str = "Y"
    note: str | None = None

    @property
    def pattern_norm(self) -> str:
        return normalize_pattern(self.match_type, self.pattern)


def normalize_pattern(match_type: str, pattern: str) -> str:
    """신호 패턴을 비교용으로 바꾼다.

    domain: 소문자, 앞뒤 점 제거.  keyword: 공백/기호를 없앤 한 덩어리 ('해외 직구' == '해외직구', 제목도 같은 방식으로
    이어 붙여 비교한다).  token: 토큰을 공백 하나로 이은 열 (토큰 단위로 일치해야 하므로 'iphone 15' 와 'iphone15' 는 다르다).
    """
    if match_type == "domain":
        return str(pattern).strip().lower().strip(".")
    tokens = tokenize(pattern)
    return "".join(tokens) if match_type == "keyword" else " ".join(tokens)


@dataclass
class ProductTables:
    catalog: list[CatalogRow] = field(default_factory=list)
    aliases: list[AliasRow] = field(default_factory=list)
    categories: list[SourcingCategoryRow] = field(default_factory=list)
    signals: list[SourcingSignalRow] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "product_catalog": len(self.catalog), "product_aliases": len(self.aliases),
            "sourcing_categories": len(self.categories), "sourcing_signals": len(self.signals),
        }


@dataclass(frozen=True)
class Issue:
    """검증/적재 중 사람이 봐야 하는 문제 하나. level: error(그 행을 쓰지 않음) | warning(쓰되 확인 필요)."""

    level: str
    table: str
    key: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"level": self.level, "table": self.table, "key": self.key, "code": self.code, "message": self.message}
