"""상품 페이지의 구조화 데이터에서 식별자를 읽는다 (JSON-LD, microdata, OpenGraph).

제목은 사람이 쓴 글이라 제조사/모델명이 불확실하다. 판매처 상품 페이지가 주는 구조화
데이터(schema.org Product)는 GTIN(바코드), MPN(제조사 부품번호), 브랜드, 모델을 기계가 읽게
적어 둔 것이라 훨씬 믿을 수 있다. 그래도 값은 검증한다: GTIN 은 체크 숫자가 맞아야 하고,
틀린 값은 버리고 기록한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import unescape
import json
import re
from typing import Any

from .gtin import is_valid_gtin, normalize_gtin

_JSONLD = re.compile(r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)
_ITEMPROP = re.compile(
    r'<(?P<tag>meta|span|div|p|td|li|a)\b[^>]*\bitemprop\s*=\s*["\'](?P<prop>[A-Za-z0-9]+)["\'][^>]*>', re.IGNORECASE
)
_CONTENT_ATTR = re.compile(r'\bcontent\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)
_META = re.compile(r'<meta\b[^>]*>', re.IGNORECASE)
_PROP_ATTR = re.compile(r'\b(?:property|name)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_GTIN_KEYS = ("gtin", "gtin8", "gtin12", "gtin13", "gtin14", "isbn")


@dataclass
class StructuredProduct:
    name: str | None = None
    brand: str | None = None
    model: str | None = None
    mpn: str | None = None
    sku: str | None = None
    gtin: str | None = None  # 체크 숫자가 맞는 14자리
    sources: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)  # 버린 값과 이유

    @property
    def found(self) -> bool:
        return any((self.gtin, self.mpn, self.model, self.name))


def _text(value: Any) -> str | None:
    if isinstance(value, dict):
        value = value.get("name") or value.get("@id")
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        cleaned = " ".join(unescape(str(value)).split())
        return cleaned or None
    return None


def _is_product(node: Any) -> bool:
    kind = node.get("@type") if isinstance(node, dict) else None
    kinds = kind if isinstance(kind, list) else [kind]
    return any(isinstance(k, str) and k.lower().endswith("product") for k in kinds)


def _walk_products(node: Any):
    if isinstance(node, list):
        for item in node:
            yield from _walk_products(item)
    elif isinstance(node, dict):
        if _is_product(node):
            yield node
        for value in node.values():
            if isinstance(value, (list, dict)):
                yield from _walk_products(value)


def _absorb(product: StructuredProduct, fields: dict[str, Any], source: str) -> None:
    def take(attr: str, value: Any) -> None:
        text = _text(value)
        if text and getattr(product, attr) is None:
            setattr(product, attr, text)

    take("name", fields.get("name"))
    take("brand", fields.get("brand"))
    take("model", fields.get("model"))
    take("mpn", fields.get("mpn"))
    take("sku", fields.get("sku"))
    for key in _GTIN_KEYS:
        raw = _text(fields.get(key))
        if raw is None:
            continue
        normalized = normalize_gtin(raw)
        if normalized:
            if product.gtin is None:
                product.gtin = normalized
        else:
            product.rejected.append(f"{key}={raw!r}: 체크 숫자가 맞지 않거나 길이가 8/12/13/14가 아니다")
    if source not in product.sources:
        product.sources.append(source)


def extract_structured_product(html: str) -> StructuredProduct:
    product = StructuredProduct()
    html = html or ""

    for block in _JSONLD.findall(html):
        try:
            data = json.loads(unescape(block).strip())
        except (json.JSONDecodeError, ValueError):
            product.rejected.append("json-ld 블록을 읽을 수 없다")
            continue
        for node in _walk_products(data):
            _absorb(product, node, "json-ld")

    micro: dict[str, str] = {}
    for match in _ITEMPROP.finditer(html):
        prop = match.group("prop")
        attrs = match.group(0)
        content = _CONTENT_ATTR.search(attrs)
        value = content.group(1) if content else None
        if value is None and match.group("tag").lower() != "meta":
            tail = html[match.end(): match.end() + 200]
            end = tail.find("<")
            value = tail[:end] if end != -1 else tail
        if value and value.strip():
            micro.setdefault(prop, value)
    if micro:
        before = (product.gtin, product.mpn, product.model, product.brand, product.name)
        _absorb(product, micro, "microdata")
        if before == (product.gtin, product.mpn, product.model, product.brand, product.name) and "microdata" in product.sources:
            product.sources.remove("microdata")

    og: dict[str, str] = {}
    for tag in _META.findall(html):
        prop = _PROP_ATTR.search(tag)
        content = _CONTENT_ATTR.search(tag)
        if prop and content:
            og[prop.group(1).lower()] = content.group(1)
    if og:
        before = (product.name, product.brand, product.gtin, product.mpn)
        _absorb(
            product,
            {
                "name": og.get("og:title"),
                "brand": og.get("product:brand"),
                "gtin": og.get("product:gtin") or og.get("og:upc") or og.get("product:ean"),
                "mpn": og.get("product:mfr_part_no"),
            },
            "opengraph",
        )
        if before == (product.name, product.brand, product.gtin, product.mpn) and "opengraph" in product.sources:
            product.sources.remove("opengraph")

    return product
