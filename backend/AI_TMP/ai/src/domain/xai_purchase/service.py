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
        return fallback_value, None, True
    matches = [
        int(token.replace(",", "")) for token in _PRICE_PATTERN.findall(page_text)
    ]
    if len(matches) == 0:
        return fallback_value, None, True
    crawled_price = max(matches)
    if fallback_value is None:
        return crawled_price, crawled_price, False
    return fallback_value, crawled_price, False


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


def _financial_status(current_balance: float, emergency_balance: float) -> str:
    if current_balance <= 0:
        return "critical"
    if emergency_balance < current_balance * 0.1:
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

    page_text, crawl_warning = _fetch_page_text(request.purchase.purchase_url)
    if crawl_warning is not None:
        seed_warnings.append(crawl_warning)
    current_price, crawled_price, price_estimated = _extract_current_price(
        page_text, stated_price
    )
    if price_estimated:
        seed_warnings.append("PRICE_ESTIMATED_FROM_REQUEST")
    if (
        stated_price is not None
        and crawled_price is not None
        and abs(crawled_price - stated_price) > max(int(stated_price * 0.2), 50000)
    ):
        seed_warnings.append("CRAWLED_PRICE_DIVERGES_FROM_REQUEST")

    window_stats, stats_warnings = _read_window_stats(current_price)
    seed_warnings.extend(stats_warnings)

    finance_profile = {
        "current_balance": float(request.finance_profile.current_balance.value or 0),
        "emergency_fund_balance": float(
            request.finance_profile.emergency_fund_balance.value or 0
        ),
        "expected_card_payment_amount": float(
            request.finance_profile.expected_card_payment_amount.value or 0
        ),
        "days_until_card_due": int(
            request.finance_profile.days_until_card_due.value or 0
        ),
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

    response = PurchaseXaiEvaluationResponse(
        requestId=request.request_id,
        purchaseRequestId=request.purchase.post_id,
        decision=str(item.get("decision", "REVIEW")),
        summary=str(
            item.get("polished_summary", "XAI evaluation summary unavailable.")
        ),
        financialEvaluation=EvaluationSection(
            status=_financial_status(
                finance_profile["current_balance"],
                finance_profile["emergency_fund_balance"],
            ),
            keyMetrics=[
                EvaluationMetric(
                    code="current_balance",
                    label="현재 잔액",
                    value=f"{int(finance_profile['current_balance']):,}원",
                ),
                EvaluationMetric(
                    code="emergency_fund_balance",
                    label="비상자금",
                    value=f"{int(finance_profile['emergency_fund_balance']):,}원",
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
                    code="requested_price_amount",
                    label="PR 요청 가격",
                    value=(
                        f"{int(stated_price):,}원" if stated_price is not None else "-"
                    ),
                ),
                EvaluationMetric(
                    code="crawled_price_candidate",
                    label="크롤링 감지 가격",
                    value=(
                        f"{int(crawled_price):,}원"
                        if crawled_price is not None
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
                value=str(evidence.get("observed_value", evidence.get("score", "-"))),
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
                targetDecision=(
                    "BUY_NOW"
                    if str(item.get("decision", "REVIEW")) != "BUY_NOW"
                    else "WAIT"
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
