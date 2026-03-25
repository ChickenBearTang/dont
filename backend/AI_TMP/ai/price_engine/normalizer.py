from __future__ import annotations

from datetime import datetime
import hashlib
import re
from typing import Any

from .schema_models import (
    PriceObservation,
    RawListing,
    RawMerchantOffer,
    RawPostDetail,
)

_NUMERIC_PATTERN = re.compile(r"[0-9,]+")
_SOURCE_RANK = {"merchant": 4, "post_detail": 3, "list": 2, "aggregator": 1}


def _to_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    compact = "".join(_NUMERIC_PATTERN.findall(raw)).replace(",", "")
    if compact == "":
        return None
    try:
        return int(compact)
    except ValueError:
        return None


def _canonical_id(merchant: RawMerchantOffer | None, listing: RawListing) -> str:
    if merchant is not None and merchant.gtin_raw:
        return f"gtin:{merchant.gtin_raw.strip()}"
    if merchant is not None and merchant.brand_raw and merchant.mpn_raw:
        return f"brand-mpn:{merchant.brand_raw.strip()}:{merchant.mpn_raw.strip()}"
    if merchant is not None and merchant.model_code_raw:
        return f"model:{merchant.model_code_raw.strip()}"
    normalized_title = " ".join((listing.title_raw or "").split()).lower()
    digest = hashlib.sha256(normalized_title.encode("utf-8")).hexdigest()[:16]
    return f"title-hash:{digest}"


def _pick_by_priority(candidates: list[tuple[str, Any]]) -> tuple[str, Any]:
    selected = max(candidates, key=lambda item: _SOURCE_RANK.get(item[0], 0))
    return selected


def merge_to_price_observation(
    listing: RawListing,
    post_detail: RawPostDetail | None,
    merchant_offer: RawMerchantOffer | None,
    *,
    observed_at: datetime,
    normalization_version: str = "v1",
) -> PriceObservation:
    listed_candidates: list[tuple[str, int | None]] = [
        ("list", _to_int(listing.price_raw))
    ]
    shipping_candidates: list[tuple[str, int | None]] = [
        ("list", _to_int(listing.shipping_raw))
    ]
    availability_candidates: list[tuple[str, str | None]] = [("list", None)]

    if post_detail is not None:
        listed_candidates.append(("post_detail", _to_int(post_detail.option_text_raw)))
        shipping_candidates.append(("post_detail", None))
        availability_candidates.append(("post_detail", post_detail.soldout_text_raw))

    if merchant_offer is not None:
        merchant_listed = _to_int(merchant_offer.sale_price_raw) or _to_int(
            merchant_offer.listed_price_raw
        )
        listed_candidates.append(("merchant", merchant_listed))
        shipping_candidates.append(
            ("merchant", _to_int(merchant_offer.shipping_fee_raw))
        )
        availability_candidates.append(("merchant", merchant_offer.availability_raw))

    source_priority, listed_price = _pick_by_priority(
        [
            (priority, value)
            for priority, value in listed_candidates
            if value is not None
        ]
        or [("list", None)]
    )
    _, shipping_fee = _pick_by_priority(
        [
            (priority, value)
            for priority, value in shipping_candidates
            if value is not None
        ]
        or [("list", None)]
    )
    _, availability_status = _pick_by_priority(
        [
            (priority, value)
            for priority, value in availability_candidates
            if value not in (None, "")
        ]
        or [("list", "unknown")]
    )

    effective_price_candidate: int | None
    if listed_price is None or shipping_fee is None:
        effective_price_candidate = None
    else:
        effective_price_candidate = listed_price + shipping_fee

    confidence = {
        "merchant": 0.95,
        "post_detail": 0.75,
        "list": 0.60,
        "aggregator": 0.40,
    }.get(source_priority, 0.50)

    evidence_refs = [
        {
            "post_url": listing.post_url,
            "merchant_url": merchant_offer.merchant_url
            if merchant_offer is not None
            else None,
            "selector": "price_or_shipping",
            "snippet": listing.price_raw,
        }
    ]

    return PriceObservation(
        canonical_product_id_candidate=_canonical_id(merchant_offer, listing),
        variant_id_candidate=None,
        seller_id_candidate=(
            merchant_offer.seller_name_raw if merchant_offer is not None else None
        ),
        observed_at=observed_at,
        listed_price=listed_price,
        shipping_fee=shipping_fee,
        effective_price_candidate=effective_price_candidate,
        availability_status=availability_status,
        stock_status=(merchant_offer.stock_raw if merchant_offer is not None else None),
        source_site=listing.source_site,
        source_priority=source_priority,
        confidence=confidence,
        evidence_refs=evidence_refs,
        normalization_version=normalization_version,
        brand=(merchant_offer.brand_raw if merchant_offer is not None else None),
        category=listing.category_raw,
        seller_type="merchant" if merchant_offer is not None else "community",
        post_url=listing.post_url,
        post_id_raw=listing.post_id_raw,
        merchant_url=(
            merchant_offer.merchant_url if merchant_offer is not None else None
        ),
        merchant_domain=(
            merchant_offer.merchant_domain if merchant_offer is not None else None
        ),
        title_raw=listing.title_raw,
        body_raw=(post_detail.body_raw if post_detail is not None else None),
        price_raw=listing.price_raw,
        shipping_raw=listing.shipping_raw,
        html_hash=listing.html_hash,
        raw_jsonld=(merchant_offer.raw_jsonld if merchant_offer is not None else None),
    )
