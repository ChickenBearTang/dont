"""제목(+상품 페이지)에서 제조사·모델 단위로 상품을 식별한다.

신뢰 순서
  1. 상품 페이지의 GTIN(바코드, 체크 숫자 검증)           -> RESOLVED_GTIN
  2. 상품 페이지의 브랜드 + MPN(제조사 부품번호)          -> RESOLVED_MPN
  3. 제목의 GTIN                                          -> RESOLVED_GTIN
  4. 카탈로그에서 버전까지 정확히 일치                    -> RESOLVED_CATALOG
  5. 제목에서 뽑은 제조사/모델 (카탈로그에 없음)          -> UNVERIFIED_MODEL
  6. LLM 이 뽑았고 제목에 그대로 있음 (검증 통과)         -> UNVERIFIED_MODEL (source=llm)
  불확실하면 고르지 않는다: AMBIGUOUS_VARIANT(버전 모호), MULTIPLE_PRODUCTS(묶음), BRAND_ONLY, UNRESOLVED.

canonical_id 는 신뢰 상태(RESOLVED_*)에서만 채운다. 신뢰하지 않는 식별로 가격 이력을 합치면
다른 모델의 가격이 한 상품의 이력에 섞이기 때문이다. group_key 는 항상 있으나 신뢰하지 않으면
'unverified:' 로 시작해 구분된다.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from .brands import BrandLexicon
from .catalog import Catalog
from .gtin import find_gtins
from .llm import LlmExtractor, verify_llm_candidate
from .structured import extract_structured_product
from .text import compact_code, tokenize


class IdentityStatus(str, Enum):
    RESOLVED_GTIN = "resolved_gtin"
    RESOLVED_MPN = "resolved_mpn"
    RESOLVED_CATALOG = "resolved_catalog"
    AMBIGUOUS_VARIANT = "ambiguous_variant"
    ACCESSORY_SUSPECTED = "accessory_suspected"
    MULTIPLE_PRODUCTS = "multiple_products"
    UNVERIFIED_MODEL = "unverified_model"
    BRAND_ONLY = "brand_only"
    UNRESOLVED = "unresolved"


_TRUSTED = {IdentityStatus.RESOLVED_GTIN, IdentityStatus.RESOLVED_MPN, IdentityStatus.RESOLVED_CATALOG}


@dataclass(frozen=True)
class ProductIdentity:
    status: IdentityStatus
    canonical_id: str | None
    group_key: str
    brand: str | None
    model: str | None
    confidence: float
    source: str
    evidence: tuple[str, ...] = ()
    candidates: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def trusted(self) -> bool:
        return self.status in _TRUSTED


# 모델명이 아닌 말. 제조사 뒤에서 이 말이 나오면 모델명 추출을 멈춘다.
_STOPWORDS = frozenset(
    "무선 유선 블루투스 마우스 키보드 헤드셋 헤드폰 이어폰 노트북 모니터 그래픽카드 그래픽 쿠폰 할인 무료배송 무배 직구 해외 카드 "
    "최저가 역대가 핫딜 정품 병행 국내 정발 개봉 새제품 미개봉 단품 세트 택배 배송 무료 원 개 정가 특가 이벤트 "
    "wireless bluetooth mouse keyboard gaming gamer headset headphone earphone earbuds laptop monitor usb free shipping official "
    "krw won coupon sale deal".split()
)
_MAX_MODEL_TOKENS = 4

# 모델명 바로 뒤에 오는 말이 상품을 바꾸는지 판단한다. 설명어는 끝이 없지만 변형어는 한정돼 있다.
#   - 변형어(mini, plus, for, v2, 미니, 프로 ...)가 오면 다른 상품일 수 있어 확정하지 않는다.
#   - 알 수 없는 '영문' 토큰도 확정하지 않는다 (s, se, xl, ti ... 변형 표기는 대개 영문이다).
#   - 알려진 설명어/색/규격/숫자, 그리고 알 수 없는 '한글' 설명어는 통과시킨다
#     (노이즈캔슬링, 충전케이스 ...). 알려지지 않은 한글 변형어는 놓칠 수 있다 — 실제 수집
#     데이터로 VARIANT_WORDS 를 늘려 가며 줄여야 하는 잔여 위험이다.
_VARIANT_WORDS = frozenset(
    "mini plus pro max ultra lite se air for edition limited special new gen "
    "미니 플러스 프로 맥스 울트라 라이트 에어 슈퍼 에디션 한정판 스페셜 신형 구형 세대 포".split()
)
_VARIANT_PATTERN = re.compile(r"^(v\d+|gen\d+|\d+세대|\d+th|mk\d+|mark\d+)$")
_BENIGN_AFTER_MODEL = _STOPWORDS | frozenset(
    "black white silver gray grey blue red pink gold green 블랙 화이트 실버 그레이 그래파이트 핑크 블루 레드 골드 그린 "
    "미드나이트 스타라이트 베이지 아이보리 한글 한국 코리아 한글각인 라이트스피드 lightspeed 신품 중고 리퍼 박스 풀박 "
    "개봉 미개봉 일반 풀 박스 magsafe 맥세이프 lightning 라이트닝 type 타입".split()
)
_SPEC_TOKEN = re.compile(r"^\d+(gb|tb|mb|mm|cm|hz|w|v|ah|mah|인치|inch|k)?$")


# 이 말이 제목 어디에든 있으면 본체가 아니라 액세서리/소모품 글일 수 있다. '충전케이스'처럼
# 본체의 일부를 말하는 합성어는 한 토큰이라 여기에 걸리지 않는다.
_ACCESSORY_WORDS = frozenset(
    "케이스 커버 필름 파우치 스킨 이어팁 거치대 스티커 호환 호환용 교체 리필 액세서리 보호필름 케이블 스트랩 "
    "case cover film pouch skin strap compatible 교체용 이어패드 이어캡 보호 패드커버".split()
)


def _accessory_hits(tokens: list[str]) -> list[str]:
    """액세서리 단어. 본체의 일부를 말하는 '충전 케이스', '케이스 포함' 은 제외한다."""
    hits: list[str] = []
    for i, token in enumerate(tokens):
        if token not in _ACCESSORY_WORDS:
            continue
        before = tokens[i - 1] if i > 0 else ""
        after = tokens[i + 1] if i + 1 < len(tokens) else ""
        if token in ("케이스", "case") and (before in ("충전", "charging", "wireless") or after in ("포함", "included", "include")):
            continue
        hits.append(token)
    return sorted(set(hits))
_PART_LETTERS = re.compile(r"^[a-z]{1,4}$")
_PART_CODE = re.compile(r"^[a-z]?\d{3,}[a-z0-9]*$")


def _skip_part_number(following: tuple[str, ...]) -> tuple[str, ...]:
    """모델명 뒤에 붙은 제조사 부품번호(SM-R510, 910-006556)를 건너뛴다."""
    tokens = list(following)
    while tokens:
        if len(tokens) >= 2 and _PART_LETTERS.match(tokens[0]) and _PART_CODE.match(tokens[1]):
            tokens = tokens[2:]  # sm r510
        elif _PART_CODE.match(tokens[0]) and any(ch.isalpha() for ch in tokens[0]) and len(tokens[0]) >= 5:
            tokens = tokens[1:]  # r510abc 같은 단일 코드
        elif len(tokens) >= 2 and tokens[0].isdigit() and len(tokens[0]) == 3 and tokens[1].isdigit() and len(tokens[1]) >= 4:
            tokens = tokens[2:]  # 910 006556
        else:
            break
    return tuple(tokens)


def _dangerous_token(token: str, brand_aliases: frozenset[str], extra_benign: frozenset[str]) -> bool:
    if token in _VARIANT_WORDS or _VARIANT_PATTERN.match(token):
        return True
    if token in _BENIGN_AFTER_MODEL or token in extra_benign or _SPEC_TOKEN.match(token) or token in brand_aliases:
        return False
    return token.isascii() and any(ch.isalpha() for ch in token)  # 알 수 없는 영문 토큰


def _dangerous_suffix(
    following: tuple[str, ...], brand_aliases: frozenset[str], extra_benign: frozenset[str] = frozenset()
) -> str | None:
    """모델명 뒤에서 상품을 바꿀 수 있는 말을 찾는다. 부품번호와 숫자/규격 토큰은 건너뛰고
    처음 나오는 의미 있는 토큰 두 개까지만 본다 (멀리 떨어진 말은 설명일 가능성이 높다)."""
    tokens = [t for t in _skip_part_number(following) if not (t.isdigit() or _SPEC_TOKEN.match(t))]
    significant: list[str] = []
    for i, token in enumerate(tokens):
        if token == "c" and i > 0 and tokens[i - 1] in ("usb", "type"):
            continue  # USB-C / Type-C
        significant.append(token)
    for token in significant[:2]:
        if _dangerous_token(token, brand_aliases, extra_benign):
            return token
    return None


def _group_key(trusted_id: str | None, brand: str | None, model: str | None, title: str) -> str:
    if trusted_id:
        return trusted_id
    code = compact_code(model) if model else compact_code(title)[:40]
    return f"unverified:{brand or '-'}:{code or '-'}"


class ProductResolver:
    def __init__(
        self,
        catalog: Catalog | None = None,
        lexicon: BrandLexicon | None = None,
        llm: LlmExtractor | None = None,
    ) -> None:
        self._catalog = catalog or Catalog.load_default()
        self._lexicon = lexicon or BrandLexicon.load()
        self._llm = llm
        self._brand_alias_set = frozenset(a for b in self._lexicon.brands() for a in self._lexicon.aliases_of(b))

    def resolve(self, title: str, *, page_html: str | None = None) -> ProductIdentity:
        title = title or ""
        warnings: list[str] = []

        if page_html:
            structured = extract_structured_product(page_html)
            warnings += [f"STRUCTURED_REJECTED: {r}" for r in structured.rejected]
            page_brand = self._brand_key(structured.brand)
            if structured.gtin:
                return self._make(
                    IdentityStatus.RESOLVED_GTIN, f"gtin:{structured.gtin}", page_brand, structured.model or structured.name,
                    0.99, "page_gtin", (f"gtin {structured.gtin} ({'+'.join(structured.sources)})",), (), tuple(warnings), title,
                )
            if structured.mpn and page_brand:
                return self._make(
                    IdentityStatus.RESOLVED_MPN, f"mpn:{page_brand}:{compact_code(structured.mpn)}", page_brand,
                    structured.model or structured.mpn, 0.9, "page_mpn", (f"brand {page_brand} + mpn {structured.mpn}",), (),
                    tuple(warnings), title,
                )

        title_gtins = find_gtins(title)
        if len(title_gtins) == 1:
            return self._make(
                IdentityStatus.RESOLVED_GTIN, f"gtin:{title_gtins[0]}", None, None, 0.95, "title_gtin",
                (f"gtin {title_gtins[0]} in title",), (), tuple(warnings), title,
            )

        brands = self._lexicon.detect(title)
        match = self._catalog.match(title, brands=brands or None)

        accessory = _accessory_hits(tokenize(title))
        if accessory and (match.entry is not None or match.candidates):
            return self._make(
                IdentityStatus.ACCESSORY_SUSPECTED, None, brands[0] if brands else None, None, 0.1, "catalog",
                (f"accessory words in title: {', '.join(accessory)}",),
                tuple(e.id for e in (match.candidates or ((match.entry,) if match.entry else ()))), tuple(warnings), title,
            )

        if match.status == "none" and brands:
            # 브랜드를 말했는데 그 브랜드의 상품이 아니다 (예: '삼성 MX Master 3S'). 맞추지 않는다.
            any_brand = self._catalog.match(title)
            if any_brand.status == "match" and any_brand.entry is not None:
                warnings.append(f"BRAND_MODEL_CONFLICT: title brand {brands} but model belongs to {any_brand.entry.brand}")
                return self._make(
                    IdentityStatus.UNRESOLVED, None, brands[0], None, 0.1, "conflict",
                    ("title brand conflicts with catalog model",), (any_brand.entry.id,), tuple(warnings), title,
                )

        next_token = (
            _dangerous_suffix(match.following, self._brand_alias_set, frozenset(match.entry.benign_suffixes))
            if match.status == "match" and match.entry is not None
            else None
        )
        if match.status == "match" and match.entry is not None and next_token is not None:
            # 모델명 뒤에 카탈로그가 모르는 말이 붙었다 (MX Keys Mini, 3S for Mac ...). 기본형으로
            # 합치면 다른 상품의 가격이 섞이므로 확정하지 않는다.
            entry = match.entry
            return self._make(
                IdentityStatus.AMBIGUOUS_VARIANT, None, entry.brand, f"{entry.model} {next_token}", 0.3, "catalog",
                (*match.evidence, f"unknown token '{next_token}' follows the model"), (entry.id,), tuple(warnings), title,
            )

        if match.status == "match" and match.entry is not None:
            entry = match.entry
            explicit = entry.brand in brands
            return self._make(
                IdentityStatus.RESOLVED_CATALOG, entry.id, entry.brand, entry.model, 0.92 if explicit else 0.8, "catalog",
                (*match.evidence, "brand in title" if explicit else "brand inferred from catalog"), (), tuple(warnings), title,
            )
        if match.status == "ambiguous_variant":
            return self._make(
                IdentityStatus.AMBIGUOUS_VARIANT, None, brands[0] if brands else None, None, 0.3, "catalog",
                match.evidence, tuple(e.id for e in match.candidates), tuple(warnings), title,
            )
        if match.status == "multiple_products":
            return self._make(
                IdentityStatus.MULTIPLE_PRODUCTS, None, brands[0] if brands else None, None, 0.2, "catalog",
                match.evidence, tuple(e.id for e in match.candidates), tuple(warnings), title,
            )

        guessed = self._guess_model(title, brands)
        if guessed is not None:
            return self._make(
                IdentityStatus.UNVERIFIED_MODEL, None, brands[0], guessed, 0.5, "title_rule",
                (f"brand {brands[0]} + model tokens {guessed!r} (not in catalog)",), (), tuple(warnings), title,
            )

        llm_identity = self._try_llm(title, brands, warnings)
        if llm_identity is not None:
            return llm_identity

        if brands:
            return self._make(
                IdentityStatus.BRAND_ONLY, None, brands[0], None, 0.2, "title_rule", ("brand only, no model",), (),
                tuple(warnings), title,
            )
        return self._make(IdentityStatus.UNRESOLVED, None, None, None, 0.0, "none", (), (), tuple(warnings), title)

    # ------------------------------------------------------------------
    def _brand_key(self, raw: object) -> str | None:
        if not isinstance(raw, str) or not raw.strip():
            return None
        found = self._lexicon.detect(raw)
        return found[0] if found else compact_code(raw) or None

    def _guess_model(self, title: str, brands: list[str]) -> str | None:
        """제조사 바로 뒤에서 숫자가 든 토큰이 나올 때까지의 말을 모델명으로 추정한다 (검증 안 됨)."""
        if not brands:
            return None
        tokens = tokenize(title)
        aliases = set(self._lexicon.aliases_of(brands[0]))
        start = next((i for i, t in enumerate(tokens) if t in aliases), None)
        if start is None:
            return None
        collected: list[str] = []
        for token in tokens[start + 1:]:
            if token in _STOPWORDS:
                if collected:
                    break
                continue
            collected.append(token)
            if len(collected) >= _MAX_MODEL_TOKENS:
                break
        if not any(any(ch.isdigit() for ch in t) for t in collected):
            return None
        # 마지막으로 숫자 토큰이 나온 곳까지만 쓴다 (뒤에 붙은 설명어 제거).
        last_digit = max(i for i, t in enumerate(collected) if any(ch.isdigit() for ch in t))
        return " ".join(collected[: last_digit + 1])

    def _try_llm(self, title: str, brands: list[str], warnings: list[str]) -> ProductIdentity | None:
        if self._llm is None:
            return None
        result = self._llm.extract(title)
        if not isinstance(result, dict):
            return None
        ok, reason = verify_llm_candidate(title, result.get("brand"), result.get("model"), self._lexicon)
        if not ok:
            warnings.append(f"LLM_REJECTED: {reason}")
            return None
        brand = self._brand_key(result.get("brand")) or (brands[0] if brands else None)
        return self._make(
            IdentityStatus.UNVERIFIED_MODEL, None, brand, str(result["model"]).strip(), 0.55, "llm",
            (f"llm extraction verified against title ({reason})",), (), tuple(warnings), title,
        )

    @staticmethod
    def _make(
        status: IdentityStatus, canonical: str | None, brand: str | None, model: str | None, confidence: float,
        source: str, evidence: tuple[str, ...], candidates: tuple[str, ...], warnings: tuple[str, ...], title: str,
    ) -> ProductIdentity:
        trusted_id = canonical if status in _TRUSTED else None
        return ProductIdentity(
            status=status, canonical_id=trusted_id, group_key=_group_key(trusted_id, brand, model, title), brand=brand,
            model=model, confidence=confidence, source=source, evidence=tuple(evidence), candidates=tuple(candidates),
            warnings=tuple(warnings),
        )
