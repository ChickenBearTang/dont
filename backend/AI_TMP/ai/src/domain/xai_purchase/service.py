from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
import urllib.request

from ai.models import CrawlResult, HotDeal
from ai.finance_engine.inference import predict_finance_signal
from ai.price_engine.inference import predict_price_signal
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


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


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
    item_name: str | None,
    purchase_url: str | None,
) -> tuple[dict[str, dict[str, float | int | None]], list[str]]:
    warnings: list[str] = []
    item_family = PostgresCrawlStore.classify_item_family(
        title=item_name,
        url=purchase_url,
    )
    dsn = None
    try:
        from config import get_env

        dsn = get_env("AI_POSTGRES_DSN")
    except Exception:
        dsn = None

    if dsn:
        try:
            store = PostgresCrawlStore(dsn)
            if item_family is None:
                warnings.append("ITEM_FAMILY_UNCLASSIFIED")
                return store.read_window_stats(), warnings
            return store.read_window_stats(item_family=item_family), warnings
        except Exception:
            warnings.append("PRICE_HISTORY_READ_FAILED")

    if item_family is None:
        warnings.append("ITEM_FAMILY_UNCLASSIFIED")
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


def _default_model_artifact_path(model_dir_name: str) -> str | None:
    candidate = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "artifacts"
        / model_dir_name
    )
    if (candidate / "model.pkl").exists() and (candidate / "metadata.json").exists():
        return str(candidate)
    return None


def _map_runtime_engines(payload: dict[str, Any]) -> RuntimeEngines:
    runtime = payload.get("runtime_engines", {}) if isinstance(payload, dict) else {}
    shap_state = runtime.get("shap", {}) if isinstance(runtime, dict) else {}
    dice_state = runtime.get("dice", {}) if isinstance(runtime, dict) else {}
    price_model_state = runtime.get("price_model", {}) if isinstance(runtime, dict) else {}
    finance_model_state = (
        runtime.get("finance_model", {}) if isinstance(runtime, dict) else {}
    )
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
        price_model=(
            str(price_model_state.get("backend", "disabled"))
            if price_model_state.get("enabled")
            else "disabled"
        ),
        finance_model=(
            str(finance_model_state.get("backend", "disabled"))
            if finance_model_state.get("enabled")
            else "disabled"
        ),
    )


def _collect_warnings(payload: dict[str, Any], seed_warnings: list[str]) -> list[str]:
    warnings = list(seed_warnings)
    runtime = payload.get("runtime_engines", {}) if isinstance(payload, dict) else {}
    for engine_name in ("shap", "dice", "price_model", "finance_model"):
        state = runtime.get(engine_name, {}) if isinstance(runtime, dict) else {}
        if not state.get("enabled", False):
            reason = state.get("reason")
            if (
                isinstance(reason, str)
                and reason
                and reason
                not in {
                    "price_model_disabled",
                    "finance_model_disabled",
                    "shap_disabled_by_config",
                    "dice_disabled_by_config",
                }
            ):
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


def _financial_status_from_model(
    *,
    finance_model_signal: dict[str, Any],
    finance_model_state: dict[str, Any],
    fallback_status: str,
) -> str:
    if not finance_model_state.get("enabled", False):
        return fallback_status
    risk_bucket = str(finance_model_signal.get("finance_model_risk_bucket", "")).lower()
    if risk_bucket == "high":
        return "critical"
    if risk_bucket == "medium":
        return "tight"
    if risk_bucket == "low":
        return "healthy"
    return fallback_status


def _price_status(current_price: int | None, avg_price: float | None) -> str:
    if current_price is None or avg_price is None or avg_price <= 0:
        return "degraded"
    if current_price <= avg_price * 0.95:
        return "favorable"
    if current_price >= avg_price * 1.05:
        return "expensive"
    return "neutral"


def _is_finance_profile_empty_for_price_only(
    request: PurchaseXaiEvaluationRequest,
    *,
    current_balance: float,
    emergency_fund_balance: float,
    savebox_balance: float,
    expected_card_payment_amount: float,
) -> bool:
    has_core_signal = any(
        value > 0.0
        for value in (
            max(current_balance, 0.0),
            max(emergency_fund_balance, 0.0),
            max(savebox_balance, 0.0),
            max(expected_card_payment_amount, 0.0),
        )
    )
    if has_core_signal:
        return False

    has_optional_signal = False
    if request.finance_profile.available_fixed_expense is not None:
        has_optional_signal = (
            _provenance_value_to_float(request.finance_profile.available_fixed_expense, 0.0)
            > 0.0
        )
    if request.finance_profile.available_fixed_income is not None:
        has_optional_signal = has_optional_signal or (
            _provenance_value_to_float(request.finance_profile.available_fixed_income, 0.0)
            > 0.0
        )
    return not has_optional_signal


def _price_only_decision(price_status: str) -> str:
    normalized = price_status.strip().lower()
    if normalized == "favorable":
        return "BUY_NOW"
    if normalized == "expensive":
        return "WAIT"
    return "REVIEW"


def _price_only_summary(decision: str, price_status: str) -> str:
    verdict_label = {
        "BUY_NOW": "구매 권장",
        "WAIT": "대기 권장",
        "REVIEW": "추가 검토",
        "NOT_RECOMMENDED": "비구매 권장",
    }.get(decision, decision)
    normalized = price_status.strip().lower()
    if decision == "BUY_NOW":
        reason = "현재 가격이 최근 평균 대비 낮거나 유리한 구간입니다."
    elif decision == "WAIT":
        reason = "현재 가격이 최근 평균 대비 높아 조정 구간을 기다리는 편이 좋습니다."
    elif normalized == "degraded":
        reason = "가격 이력 데이터가 부족해 가격 신호를 충분히 비교하기 어렵습니다."
    else:
        reason = "현재 가격이 평균 수준과 유사해 추가 관찰이 필요합니다."
    return (
        f"{verdict_label}. 핵심 근거: {reason} "
        "개선 포인트: 재무 데이터가 부족해 가격 중심으로 판단했으며, "
        "재무 데이터 확보 후 재평가를 권장합니다."
    )


def _price_only_top_factors(
    *,
    price_status: str,
    current_price: int | None,
    avg_price: float | None,
) -> list[TopFactor]:
    normalized = price_status.strip().lower()
    if normalized == "favorable":
        label = "현재 가격이 최근 평균 대비 낮게 형성되어 있습니다."
        direction = "positive"
        impact = 0.2
    elif normalized == "expensive":
        label = "현재 가격이 최근 평균 대비 높게 형성되어 있습니다."
        direction = "negative"
        impact = 0.2
    elif normalized == "degraded":
        label = "가격 이력 데이터가 부족해 가격 비교 신호가 약합니다."
        direction = "negative"
        impact = 0.15
    else:
        label = "현재 가격이 최근 평균과 유사한 수준입니다."
        direction = "positive"
        impact = 0.1

    if (
        current_price is not None
        and isinstance(avg_price, (int, float))
        and float(avg_price) > 0.0
    ):
        ratio = abs((float(current_price) / float(avg_price)) - 1.0)
        impact = max(impact, min(ratio, 0.35))

    return [
        TopFactor(
            code="PRICE_ONLY_FALLBACK",
            label=label,
            direction=direction,
            impact=impact,
        )
    ]


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

    current_price = stated_price
    price_estimated = False

    window_stats, stats_warnings = _read_window_stats(
        current_price,
        request.purchase.item_name,
        request.purchase.purchase_url,
    )
    seed_warnings.extend(stats_warnings)
    price_model_path = _default_model_artifact_path("price_retrain_model")
    price_model_signal, price_model_state = predict_price_signal(
        current_price=current_price,
        window_stats=window_stats,
        category=request.purchase.category,
        explicit_model_path=price_model_path,
        enabled=True,
    )

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
        0.0,
    )
    available_fixed_income = _provenance_value_to_float(
        request.finance_profile.available_fixed_income,
        1_000_000.0,
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
    finance_model_signal, finance_model_state = predict_finance_signal(
        current_price=current_price,
        finance_profile=finance_profile,
        window_stats=window_stats,
        enabled=True,
    )
    purchase_url = (
        request.purchase.purchase_url
        or f"https://purchase-request.local/{request.purchase.post_id}"
    )
    heavy_xai_enabled = _env_flag("AI_XAI_HEAVY_ENABLED", False)
    shap_enabled = _env_flag("AI_XAI_SHAP_ENABLED", True)
    dice_enabled = _env_flag("AI_XAI_DICE_ENABLED", heavy_xai_enabled)

    fallback_counterfactual_engine = CounterfactualEngine()
    dice_engine: Any = fallback_counterfactual_engine
    if dice_enabled:
        dice_engine = DiceCounterfactualEngine(
            fallback_engine=fallback_counterfactual_engine
        )
    shap_engine: Any = ShapContributionEngine() if shap_enabled else object()

    analyzer = ExplainabilityAnalyzer(
        finance_profile=finance_profile,
        price_model_signal=price_model_signal,
        finance_model_signal=finance_model_signal,
        counterfactual_engine=fallback_counterfactual_engine,
        dice_counterfactual_engine=dice_engine,
        shap_contribution_engine=shap_engine,
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
    runtime_payload = payload.get("runtime_engines")
    if isinstance(runtime_payload, dict):
        if not shap_enabled:
            runtime_payload["shap"] = {
                "enabled": False,
                "backend": "disabled",
                "reason": "shap_disabled_by_config",
            }
        if not dice_enabled:
            runtime_payload["dice"] = {
                "enabled": False,
                "backend": "disabled",
                "reason": "dice_disabled_by_config",
            }
        runtime_payload["price_model"] = price_model_state
        runtime_payload["finance_model"] = finance_model_state
    else:
        payload["runtime_engines"] = {
            "shap": {
                "enabled": False,
                "backend": "disabled",
                "reason": "shap_disabled_by_config",
            }
            if not shap_enabled
            else {},
            "dice": {
                "enabled": False,
                "backend": "disabled",
                "reason": "dice_disabled_by_config",
            }
            if not dice_enabled
            else {},
            "price_model": price_model_state,
            "finance_model": finance_model_state,
        }

    item = payload["crawl"]["items"][0]
    runtime_engines = _map_runtime_engines(payload)
    warnings = _collect_warnings(payload, seed_warnings)
    avg_price = (
        ((window_stats.get("30d", {}) or {}).get("avg_price"))
        if isinstance(window_stats, dict)
        else None
    )
    price_status = _price_status(
        current_price,
        avg_price if isinstance(avg_price, (int, float)) else None,
    )
    decision_confidence = float(item.get("decision_confidence", 0.0))
    projected_savebox_balance_after_purchase = (
        float(finance_profile["savebox_balance"])
        - float(current_price if current_price is not None else 0)
    )
    fallback_financial_status = _financial_status(
        savebox_balance=finance_profile["savebox_balance"],
        available_fixed_expense=finance_profile["available_fixed_expense"],
        available_fixed_income=finance_profile["available_fixed_income"],
        days_until_card_due=int(finance_profile["days_until_card_due"]),
    )
    financial_status = _financial_status_from_model(
        finance_model_signal=finance_model_signal,
        finance_model_state=finance_model_state,
        fallback_status=fallback_financial_status,
    )
    decision = str(item.get("decision", "REVIEW"))
    summary = str(item.get("polished_summary", "XAI summary unavailable."))
    top_factors = [
        TopFactor(
            code=str(reason.get("reason_code", "factor")),
            label=str(reason.get("reason_text", reason.get("feature", "factor"))),
            direction="positive"
            if float(reason.get("score", 0.0)) >= 0
            else "negative",
            impact=abs(float(reason.get("score", 0.0))),
        )
        for reason in item.get("reasons", [])[:4]
    ]
    supporting_evidence = [
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
            estimationMethod=("page_text_closest_numeric" if price_estimated else None),
        )
        for evidence in item.get("supporting_evidence", [])
    ]
    counterfactuals = [
        Counterfactual(
            label=str(counterfactual.get("message", "대체 조건을 확인하세요.")),
            targetDecision=_counterfactual_target_decision(
                current_decision=decision,
                counterfactual=counterfactual,
            ),
            validated=str(counterfactual.get("type", "")) == "dice",
        )
        for counterfactual in item.get("counterfactuals", [])[:3]
    ]

    if _is_finance_profile_empty_for_price_only(
        request,
        current_balance=current_balance,
        emergency_fund_balance=emergency_fund_balance,
        savebox_balance=savebox_balance,
        expected_card_payment_amount=expected_card_payment_amount,
    ):
        if "FINANCE_PROFILE_EMPTY_FALLBACK" not in warnings:
            warnings.append("FINANCE_PROFILE_EMPTY_FALLBACK")
        decision = _price_only_decision(price_status)
        summary = _price_only_summary(decision, price_status)
        top_factors = _price_only_top_factors(
            price_status=price_status,
            current_price=current_price,
            avg_price=avg_price if isinstance(avg_price, (int, float)) else None,
        )
        supporting_evidence = [
            evidence
            for evidence in supporting_evidence
            if "price" in evidence.field.lower()
        ]
        counterfactuals = []
        financial_status = "degraded"
        decision_confidence = min(decision_confidence, 0.55)

    response = PurchaseXaiEvaluationResponse(
        requestId=request.request_id,
        purchaseRequestId=request.purchase.post_id,
        decision=decision,
        summary=summary,
        financialEvaluation=EvaluationSection(
            status=financial_status,
            keyMetrics=[
                EvaluationMetric(
                    code="savebox_balance",
                    label="세이브박스 잔액",
                    value=f"{int(finance_profile['savebox_balance']):,}원",
                ),
                EvaluationMetric(
                    code="available_fixed_expense",
                    label="이번 달 고정지출",
                    value=f"{int(finance_profile['available_fixed_expense']):,}원",
                ),
                EvaluationMetric(
                    code="available_fixed_income",
                    label="이번 달 고정 수입",
                    value=f"{int(finance_profile['available_fixed_income']):,}원",
                ),
                EvaluationMetric(
                    code="expected_card_payment_amount",
                    label="이번 달 카드지출 합계",
                    value=f"{int(finance_profile['expected_card_payment_amount']):,}원",
                ),
                EvaluationMetric(
                    code="days_until_card_due",
                    label="카드 결제일까지",
                    value=f"{int(finance_profile['days_until_card_due'])}일",
                ),
            ],
        ),
        priceEvaluation=EvaluationSection(
            status=price_status,
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
        topFactors=top_factors,
        supportingEvidence=supporting_evidence,
        counterfactuals=counterfactuals,
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
