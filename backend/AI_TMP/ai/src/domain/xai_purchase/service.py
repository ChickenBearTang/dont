from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlparse
import urllib.request

from ai.models import CrawlResult, HotDeal
from ai.xai.analyzer import ExplainabilityAnalyzer
from ai.xai.counterfactuals import CounterfactualEngine
from ai.xai.dice_engine import DiceCounterfactualEngine
from ai.xai.shap_engine import ShapContributionEngine
from domain.xai_purchase.audit_store import JsonlXaiAuditLogStore
from domain.xai_purchase.schemas import (
    ConfidenceSection,
    Counterfactual,
    EvaluationMetric,
    EvaluationSection,
    PurchaseXaiEvaluationRequest,
    PurchaseXaiEvaluationResponse,
    RuntimeEngines,
    SupportingEvidence,
    TopFactor,
)
from ai.storage.postgres_store import PostgresCrawlStore

_PRICE_PATTERN = re.compile(r"(?<!\d)(\d{1,3}(?:,\d{3})+|\d{5,9})(?!\d)")
_TAG_PRICE_BLOCK_PATTERN = re.compile(
    r"<(?P<tag>[a-z0-9]+)[^>]*(?:class|id|itemprop|data-testid|data-role|aria-label)\s*=\s*(['\"])"
    r"[^\"']*(?:price|가격|금액)[^\"']*\2[^>]*>(?P<body>.*?)</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
_META_PRICE_CONTENT_PATTERN = re.compile(
    r"<meta[^>]*(?:property|name|itemprop)\s*=\s*(['\"])"
    r"[^\"']*price[^\"']*\1[^>]*content\s*=\s*(['\"])(?P<content>[^\"']+)\2[^>]*"
    r"|<meta[^>]*content\s*=\s*(['\"])(?P<content_alt>[^\"']+)\3[^>]*"
    r"(?:property|name|itemprop)\s*=\s*(['\"])[^\"']*price[^\"']*\4[^>]*",
    re.IGNORECASE,
)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_GENERIC_NUMBER_TOKEN_PATTERN = re.compile(r"\d[\d,]{0,11}")
_TOTAL_PRICE_HINT_PATTERN = re.compile(
    r"(총\s*(?:액|합|금액|결제)?|합계|전체\s*금액|누적|subtotal|total)",
    re.IGNORECASE,
)
_UNIT_PRICE_HINT_PATTERN = re.compile(
    r"(판매가|구매가|할인가|최종가|즉시가|단가|개당|price|가격|금액)",
    re.IGNORECASE,
)
_QUANTITY_TOKEN_PATTERN = re.compile(r"(\d{1,5})\s*(개|입|ea|pcs)", re.IGNORECASE)
_AUDIT_STORE = JsonlXaiAuditLogStore()


def _fetch_page_text(url: str | None) -> tuple[str | None, str | None]:
    if url is None or url.strip() == "":
        return None, "MISSING_PURCHASE_URL"
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            text = response.read().decode("utf-8", errors="ignore")
            return text[:20000], None
    except Exception:
        return None, "CRAWL_FETCH_FAILED"


def _extract_current_price(
    page_text: str | None, fallback_value: int | None
) -> tuple[int | None, int | None, bool]:
    if page_text is None:
        return fallback_value, 0, True

    tagged_price = _extract_price_from_tagged_html(
        page_text=page_text,
        fallback_value=fallback_value,
    )
    if tagged_price is not None:
        if fallback_value is None:
            return tagged_price, tagged_price, False
        return fallback_value, tagged_price, False

    matches = [
        int(token.replace(",", "")) for token in _PRICE_PATTERN.findall(page_text)
    ]
    if len(matches) == 0:
        return fallback_value, 0, True
    crawled_price = max(matches)
    if fallback_value is None:
        return crawled_price, crawled_price, False
    return fallback_value, crawled_price, False


def _extract_price_from_tagged_html(
    *,
    page_text: str,
    fallback_value: int | None,
) -> int | None:
    candidates: list[tuple[int, int, int]] = []
    candidate_order = 0

    for meta_match in _META_PRICE_CONTENT_PATTERN.finditer(page_text):
        content = meta_match.group("content") or meta_match.group("content_alt")
        context = _strip_html_tags(meta_match.group(0))
        parsed = _parse_positive_int(content)
        if parsed is not None:
            candidate_order += 1
            score = _score_tagged_candidate(
                value=parsed,
                context=context,
                near_text=context,
            )
            candidates.append((parsed, score, candidate_order))
            for derived in _derive_unit_prices_from_total(parsed, context=context):
                candidate_order += 1
                candidates.append((derived, score + 2, candidate_order))

    for block_match in _TAG_PRICE_BLOCK_PATTERN.finditer(page_text):
        context = _strip_html_tags(block_match.group(0))
        for value, near_text in _extract_numeric_tokens_with_context(context):
            candidate_order += 1
            score = _score_tagged_candidate(
                value=value,
                context=context,
                near_text=near_text,
            )
            candidates.append((value, score, candidate_order))
            for derived in _derive_unit_prices_from_total(value, context=context):
                candidate_order += 1
                candidates.append((derived, score + 2, candidate_order))

    if len(candidates) == 0:
        return None

    if fallback_value is not None and fallback_value > 0:
        return min(
            candidates,
            key=lambda candidate: (
                abs(candidate[0] - fallback_value),
                -candidate[1],
                candidate[2],
            ),
        )[0]

    best_score = max(score for _, score, _ in candidates)
    best_candidates = [
        (value, score, order)
        for value, score, order in candidates
        if score == best_score
    ]
    return min(best_candidates, key=lambda candidate: (candidate[0], candidate[2]))[0]


def _strip_html_tags(value: str) -> str:
    return _HTML_TAG_PATTERN.sub(" ", value)


def _extract_numeric_tokens_with_context(value: str) -> list[tuple[int, str]]:
    parsed_values: list[tuple[int, str]] = []
    for token_match in _GENERIC_NUMBER_TOKEN_PATTERN.finditer(value):
        parsed = _parse_positive_int(token_match.group(0))
        if parsed is None:
            continue
        start = max(0, token_match.start() - 12)
        end = min(len(value), token_match.end() + 12)
        near_text = value[start:end]
        parsed_values.append((parsed, near_text))
    return parsed_values


def _extract_quantity_hint(context: str) -> int | None:
    quantity_match = _QUANTITY_TOKEN_PATTERN.search(context)
    if quantity_match is None:
        return None
    quantity = int(quantity_match.group(1))
    if quantity <= 1:
        return None
    return quantity


def _derive_unit_prices_from_total(value: int, *, context: str) -> list[int]:
    if not _TOTAL_PRICE_HINT_PATTERN.search(context):
        return []
    quantity = _extract_quantity_hint(context)
    if quantity is None or value <= quantity:
        return []
    if value < (quantity * 10):
        return []
    return [max(int(round(value / quantity)), 1)]


def _score_tagged_candidate(*, value: int, context: str, near_text: str) -> int:
    score = 0
    near_text_lower = near_text.lower()
    if "원" in near_text or "krw" in near_text_lower:
        score += 3
    if _UNIT_PRICE_HINT_PATTERN.search(context):
        score += 2
    if _TOTAL_PRICE_HINT_PATTERN.search(context):
        score -= 3
    if _QUANTITY_TOKEN_PATTERN.search(near_text) and "원" not in near_text:
        score -= 2
    if value > 100_000_000:
        score -= 1
    if value < 100:
        score -= 2
    return score


def _parse_positive_int(value: str | None) -> int | None:
    if value is None:
        return None
    digits = re.sub(r"[^0-9]", "", value)
    if digits == "":
        return None
    parsed = int(digits)
    if parsed <= 0:
        return None
    return parsed


def _provenance_value_to_float(value_obj: Any | None, default: float = 0.0) -> float:
    if value_obj is None:
        return float(default)
    raw_value = getattr(value_obj, "value", None)
    if raw_value is None:
        return float(default)
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return float(default)


def _provenance_value_to_int(value_obj: Any | None, default: int = 0) -> int:
    if value_obj is None:
        return int(default)
    raw_value = getattr(value_obj, "value", None)
    if raw_value is None:
        return int(default)
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return int(default)


def _read_window_stats(
    price_value: int | None,
) -> tuple[dict[str, dict[str, float | int | None]], list[str]]:
    warnings: list[str] = []
    dsn = None
    try:
        from config import get_env

        dsn = get_env("AI_POSTGRES_DSN")
    except Exception:
        dsn = None

    if dsn:
        try:
            store = PostgresCrawlStore(dsn)
            return store.read_window_stats(), warnings
        except Exception:
            warnings.append("PRICE_HISTORY_READ_FAILED")

    warnings.append("NO_PRICE_HISTORY")
    base_price = (
        float(price_value) if price_value is not None and price_value > 0 else None
    )
    return {
        "30d": {
            "count": 1 if base_price is not None else 0,
            "avg_price": base_price,
            "min_price": base_price,
            "max_price": base_price,
        }
    }, warnings


def _map_runtime_engines(payload: dict[str, Any]) -> RuntimeEngines:
    runtime = payload.get("runtime_engines", {}) if isinstance(payload, dict) else {}
    shap_state = runtime.get("shap", {}) if isinstance(runtime, dict) else {}
    dice_state = runtime.get("dice", {}) if isinstance(runtime, dict) else {}
    return RuntimeEngines(
        decision="rule_engine_v1",
        explanation="rule_trace",
        shap=(
            str(shap_state.get("backend", "disabled"))
            if shap_state.get("enabled")
            else "disabled"
        ),
        dice=(
            str(dice_state.get("backend", "disabled"))
            if dice_state.get("enabled")
            else "disabled"
        ),
    )


def _collect_warnings(payload: dict[str, Any], seed_warnings: list[str]) -> list[str]:
    warnings = list(seed_warnings)
    runtime = payload.get("runtime_engines", {}) if isinstance(payload, dict) else {}
    for engine_name in ("shap", "dice"):
        state = runtime.get(engine_name, {}) if isinstance(runtime, dict) else {}
        if not state.get("enabled", False):
            reason = state.get("reason")
            if isinstance(reason, str) and reason:
                warnings.append(reason.upper())
    errors = payload.get("errors", [])
    if isinstance(errors, list):
        for error in errors:
            if isinstance(error, dict):
                code = error.get("code")
                if isinstance(code, str) and code:
                    warnings.append(code)

    deduped: list[str] = []
    seen: set[str] = set()
    for warning in warnings:
        if warning in seen:
            continue
        seen.add(warning)
        deduped.append(warning)
    return deduped


def _data_completeness(warnings: list[str]) -> float:
    penalties = 0.0
    for warning in warnings:
        if warning in {
            "MISSING_PURCHASE_URL",
            "CRAWL_FETCH_FAILED",
            "NO_PRICE_HISTORY",
        }:
            penalties += 0.2
        elif warning.endswith("UNAVAILABLE") or warning.endswith("FAILED"):
            penalties += 0.1
    return max(0.0, min(1.0, 1.0 - penalties))


def _explanation_fidelity(
    warnings: list[str], runtime_engines: RuntimeEngines
) -> float:
    score = 0.9
    if runtime_engines.shap == "disabled":
        score -= 0.1
    if runtime_engines.dice == "disabled":
        score -= 0.1
    if any(
        warning in {"MISSING_PURCHASE_URL", "NO_PRICE_HISTORY"} for warning in warnings
    ):
        score -= 0.15
    return max(0.0, min(1.0, score))


def _financial_status(
    *,
    savebox_balance: float,
    available_fixed_expense: float,
    available_fixed_income: float,
    days_until_card_due: int,
) -> str:
    safe_savebox = max(float(savebox_balance), 0.0)
    safe_fixed_expense = max(float(available_fixed_expense), 0.0)
    safe_fixed_income = max(float(available_fixed_income), 0.0)
    safe_due_days = max(int(days_until_card_due), 0)

    cashflow_margin = safe_fixed_income - safe_fixed_expense

    if safe_savebox <= 0 and (cashflow_margin <= 0 or safe_due_days <= 14):
        return "critical"

    if cashflow_margin < 0:
        if safe_due_days <= 14 or safe_savebox < abs(cashflow_margin):
            return "tight"

    if safe_due_days <= 7 and safe_savebox < max(safe_fixed_expense, 1.0):
        return "tight"
    if safe_due_days <= 14 and safe_savebox < max(safe_fixed_expense * 0.5, 1.0):
        return "tight"

    return "healthy"


def _price_status(current_price: int | None, avg_price: float | None) -> str:
    if current_price is None or avg_price is None or avg_price <= 0:
        return "degraded"
    if current_price <= avg_price * 0.95:
        return "favorable"
    if current_price >= avg_price * 1.05:
        return "expensive"
    return "neutral"


def _safe_non_negative_int(value: Any, default: int = 0) -> int:
    try:
        return max(int(float(value)), 0)
    except (TypeError, ValueError):
        return int(default)


def _counterfactual_target_decision(
    *, current_decision: str, counterfactual: dict[str, Any]
) -> str:
    action = str(counterfactual.get("action", ""))
    change = _safe_non_negative_int(counterfactual.get("suggested_change", 0))
    normalized_current = (
        current_decision
        if current_decision in {"BUY_NOW", "WAIT", "REVIEW", "NOT_RECOMMENDED"}
        else "REVIEW"
    )

    if action == "wait_for_better_price":
        return "WAIT"
    if change <= 0:
        return normalized_current
    if normalized_current in {"WAIT", "REVIEW"}:
        return "BUY_NOW"
    if normalized_current == "NOT_RECOMMENDED":
        return "REVIEW"
    return normalized_current


def evaluate_pr_purchase_xai(
    request: PurchaseXaiEvaluationRequest,
) -> PurchaseXaiEvaluationResponse:
    seed_warnings: list[str] = []
    stated_price_value = request.purchase.price_amount.value
    stated_price = (
        int(stated_price_value)
        if isinstance(stated_price_value, (int, float))
        else None
    )

    # Product page crawling is intentionally disabled for PR XAI.
    # Current price is treated as the submitted PR request price.
    current_price = stated_price
    price_estimated = False

    window_stats, stats_warnings = _read_window_stats(current_price)
    seed_warnings.extend(stats_warnings)

    current_balance = _provenance_value_to_float(
        request.finance_profile.current_balance
    )
    emergency_fund_balance = _provenance_value_to_float(
        request.finance_profile.emergency_fund_balance
    )
    expected_card_payment_amount = _provenance_value_to_float(
        request.finance_profile.expected_card_payment_amount
    )
    days_until_card_due = _provenance_value_to_int(
        request.finance_profile.days_until_card_due
    )
    savebox_balance = _provenance_value_to_float(
        request.finance_profile.savebox_balance,
        emergency_fund_balance,
    )
    available_fixed_expense = _provenance_value_to_float(
        request.finance_profile.available_fixed_expense,
        expected_card_payment_amount,
    )
    available_fixed_income = _provenance_value_to_float(
        request.finance_profile.available_fixed_income,
        0.0,
    )

    finance_profile = {
        "current_balance": current_balance,
        "emergency_fund_balance": emergency_fund_balance,
        "expected_card_payment_amount": expected_card_payment_amount,
        "days_until_card_due": days_until_card_due,
        "savebox_balance": savebox_balance,
        "available_fixed_expense": available_fixed_expense,
        "available_fixed_income": available_fixed_income,
    }
    purchase_url = (
        request.purchase.purchase_url
        or f"https://purchase-request.local/{request.purchase.post_id}"
    )

    fallback_counterfactual_engine = CounterfactualEngine()
    analyzer = ExplainabilityAnalyzer(
        finance_profile=finance_profile,
        counterfactual_engine=fallback_counterfactual_engine,
        dice_counterfactual_engine=DiceCounterfactualEngine(
            fallback_engine=fallback_counterfactual_engine
        ),
        shap_contribution_engine=ShapContributionEngine(),
    )
    payload = analyzer.analyze_crawl_result(
        CrawlResult(
            source=urlparse(purchase_url).netloc or "purchase-request",
            fetched_at=datetime.now(timezone.utc),
            items=[
                HotDeal(
                    title=request.purchase.item_name,
                    url=purchase_url,
                    price=str(current_price) if current_price is not None else None,
                )
            ],
        ),
        top_k=3,
        window_stats=window_stats,
    )

    item = payload["crawl"]["items"][0]
    runtime_engines = _map_runtime_engines(payload)
    warnings = _collect_warnings(payload, seed_warnings)
    avg_price = (
        ((window_stats.get("30d", {}) or {}).get("avg_price"))
        if isinstance(window_stats, dict)
        else None
    )
    decision_confidence = float(item.get("decision_confidence", 0.0))
    projected_savebox_balance_after_purchase = (
        float(finance_profile["savebox_balance"])
        - float(current_price if current_price is not None else 0)
    )

    response = PurchaseXaiEvaluationResponse(
        requestId=request.request_id,
        purchaseRequestId=request.purchase.post_id,
        decision=str(item.get("decision", "REVIEW")),
        summary=str(
            item.get("polished_summary", "XAI 평가 요약을 생성하지 못했습니다.")
        ),
        financialEvaluation=EvaluationSection(
            status=_financial_status(
                savebox_balance=finance_profile["savebox_balance"],
                available_fixed_expense=finance_profile["available_fixed_expense"],
                available_fixed_income=finance_profile["available_fixed_income"],
                days_until_card_due=int(finance_profile["days_until_card_due"]),
            ),
            keyMetrics=[
                EvaluationMetric(
                    code="savebox_balance",
                    label="세이브박스 잔액",
                    value=f"{int(finance_profile['savebox_balance']):,}원",
                ),
                EvaluationMetric(
                    code="available_fixed_expense",
                    label="사용가능 고정 지출",
                    value=f"{int(finance_profile['available_fixed_expense']):,}원",
                ),
                EvaluationMetric(
                    code="available_fixed_income",
                    label="사용가능 고정 수입",
                    value=f"{int(finance_profile['available_fixed_income']):,}원",
                ),
                EvaluationMetric(
                    code="days_until_card_due",
                    label="카드 결제일까지",
                    value=f"{int(finance_profile['days_until_card_due'])}일",
                ),
            ],
        ),
        priceEvaluation=EvaluationSection(
            status=_price_status(
                current_price,
                avg_price if isinstance(avg_price, (int, float)) else None,
            ),
            keyMetrics=[
                EvaluationMetric(
                    code="current_effective_price",
                    label="현재 판단 가격",
                    value=(
                        f"{int(current_price):,}원"
                        if current_price is not None
                        else "-"
                    ),
                ),
                EvaluationMetric(
                    code="avg_price_30d",
                    label="30일 평균가",
                    value=(
                        f"{int(avg_price):,}원"
                        if isinstance(avg_price, (int, float))
                        else "-"
                    ),
                ),
            ],
        ),
        topFactors=[
            TopFactor(
                code=str(reason.get("reason_code", "factor")),
                label=str(reason.get("reason_text", reason.get("feature", "요인"))),
                direction="positive"
                if float(reason.get("score", 0.0)) >= 0
                else "negative",
                impact=abs(float(reason.get("score", 0.0))),
            )
            for reason in item.get("reasons", [])[:4]
        ],
        supportingEvidence=[
            SupportingEvidence(
                field=str(evidence.get("feature", "unknown")),
                value=(
                    str(int(projected_savebox_balance_after_purchase))
                    if str(evidence.get("feature", "")) == "projected_balance_after_purchase"
                    else str(evidence.get("observed_value", evidence.get("score", "-")))
                ),
                source=(
                    request.purchase.price_amount.source
                    if str(evidence.get("feature", "")) == "current_price"
                    else "fastapi.xai"
                ),
                snapshotId=(
                    request.purchase.price_amount.snapshot_id
                    if str(evidence.get("feature", "")) == "current_price"
                    else str(item.get("data_snapshot_id", ""))
                ),
                isDefault=False,
                isEstimated=str(evidence.get("feature", "")) == "current_price"
                and price_estimated,
                estimationMethod=(
                    "page_text_closest_numeric" if price_estimated else None
                ),
            )
            for evidence in item.get("supporting_evidence", [])
        ],
        counterfactuals=[
            Counterfactual(
                label=str(counterfactual.get("message", "대체 조건을 확인하세요.")),
                targetDecision=_counterfactual_target_decision(
                    current_decision=str(item.get("decision", "REVIEW")),
                    counterfactual=counterfactual,
                ),
                validated=str(counterfactual.get("type", "")) == "dice",
            )
            for counterfactual in item.get("counterfactuals", [])[:3]
        ],
        warnings=warnings,
        confidence=ConfidenceSection(
            decisionConfidence=decision_confidence,
            dataCompleteness=_data_completeness(warnings),
            explanationFidelity=_explanation_fidelity(warnings, runtime_engines),
        ),
        runtimeEngines=runtime_engines,
        generatedAt=datetime.now(timezone.utc),
        schemaVersion=request.schema_version,
        modelVersion=str(payload.get("model_version"))
        if payload.get("model_version")
        else None,
        ruleVersion=str(payload.get("rule_version"))
        if payload.get("rule_version")
        else None,
    )
    _AUDIT_STORE.save(
        request_id=request.request_id,
        purchase_request_id=request.purchase.post_id,
        warnings=warnings,
        runtime_engines=response.runtime_engines.model_dump(by_alias=True),
        audit_logs=list(payload.get("audit_logs", [])),
    )
    return response
