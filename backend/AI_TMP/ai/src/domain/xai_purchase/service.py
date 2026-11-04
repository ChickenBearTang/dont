from __future__ import annotations

from datetime import date, datetime, timezone
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
from ai.xai.input_contract import (
    FINANCE_PROFILE_FIELDS,
    Origin,
    RawField,
    ResolvedFinanceProfile,
    resolve_finance_profile,
)
from ai.xai.shap_engine import ShapContributionEngine
from ai.xai.spending import (
    RecentTransaction,
    SpendingEstimate,
    estimate_monthly_spending,
)
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

# 입력 계약의 출처 정보가 신뢰도(dataCompleteness)에 미치는 감점.
_DEFAULTED_FIELD_PENALTY = 0.05
_ESTIMATED_FIELD_PENALTY = 0.02

# analyzer 가 내놓는 근거(feature) 이름 -> 그 값이 유래한 재무 프로필 필드.
# 근거에 isDefault / isEstimated 를 정직하게 표시하기 위한 매핑이다.
_FEATURE_TO_PROFILE_FIELD = {
    "emergency_fund_balance": "emergency_fund_balance",
    "projected_balance_after_purchase": "savebox_balance",
    "days_until_card_due": "days_until_card_due",
}


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


def _utc_today() -> date:
    """월 지출 창의 기준일. 테스트가 고정할 수 있도록 함수로 분리했다."""
    return datetime.now(timezone.utc).date()


def _estimate_request_spending(
    request: PurchaseXaiEvaluationRequest,
    *,
    as_of: date | None = None,
) -> SpendingEstimate:
    """recentTransactions 에서 최근 30일 지출을 계산한다.

    예전에는 크롤링한 핫딜의 평균가 x 건수로 월 지출을 대신했다.
    """
    transactions = [
        RecentTransaction(
            transaction_date=transaction.transaction_date,
            amount=transaction.transaction_amount,
        )
        for transaction in request.recent_transactions
    ]
    return estimate_monthly_spending(transactions, as_of=as_of or _utc_today())


def _resolve_finance(
    request: PurchaseXaiEvaluationRequest,
    *,
    as_of: date | None = None,
) -> tuple[ResolvedFinanceProfile, SpendingEstimate]:
    """요청의 재무 프로필을 입력 계약에 통과시킨다.

    필수 필드가 없거나 숫자가 아니면 InputContractViolation 이 발생한다.
    예전에는 이 자리에서 0 이나 기본값이 조용히 들어갔다.

    전송 스키마의 필드명 -> 내부 이름 매핑은 계약의 FieldSpec 이름과 pydantic
    속성명이 같다는 규칙으로 파생하므로 별도 매핑 표를 두지 않는다. 월 지출은
    Spring 이 숫자로 보내지 않으므로 거래 목록에서 계산해 끼워 넣는다. 잘렸을
    가능성이 있으면(하한값) 추정값으로, 알 수 없으면 비워서 기본값 + 기록으로
    남긴다.
    """
    raw: dict[str, RawField | None] = {}
    for spec in FINANCE_PROFILE_FIELDS:
        provenance = getattr(request.finance_profile, spec.name, None)
        if provenance is None:
            raw[spec.name] = None
            continue
        raw[spec.name] = RawField(
            value=provenance.value,
            is_default=provenance.is_default,
            is_estimated=provenance.is_estimated,
        )

    spending = _estimate_request_spending(request, as_of=as_of)
    if spending.amount is not None:
        raw["monthly_spending_30d"] = RawField(
            value=spending.amount, is_estimated=spending.truncated
        )
    return resolve_finance_profile(raw, strict=True), spending


def _resolve_request_finance_profile(
    request: PurchaseXaiEvaluationRequest,
    *,
    as_of: date | None = None,
) -> ResolvedFinanceProfile:
    return _resolve_finance(request, as_of=as_of)[0]


def _spending_warnings(spending: SpendingEstimate) -> list[str]:
    warnings: list[str] = []
    if spending.amount is None:
        warnings.append(f"SPENDING_UNKNOWN:{spending.reason}")
    if spending.truncated:
        # Spring 은 최근 50건만 보낸다. 합계는 실제보다 작을 수 있는 하한값이다.
        warnings.append("SPENDING_TRUNCATED")
    return warnings


def _evidence_origin(feature: str, profile: ResolvedFinanceProfile) -> str | None:
    """근거(feature) 하나가 유래한 재무 필드의 출처. 재무 필드가 아니면 None."""
    field_name = _FEATURE_TO_PROFILE_FIELD.get(feature)
    if field_name is None:
        return None
    return profile.origins.get(field_name)


def _unmapped_origin_evidence(
    profile: ResolvedFinanceProfile,
    finance_profile: dict[str, float | int],
) -> list[SupportingEvidence]:
    """기본값/추정값인데 어느 근거(feature)에도 연결되지 않은 필드를 근거로 노출한다.

    고정 수입/지출처럼 모델 입력으로만 쓰이는 필드는 근거 목록에 나타나지 않아,
    기본값이 판단에 들어갔다는 사실이 응답에서 보이지 않았다.
    """
    mapped = set(_FEATURE_TO_PROFILE_FIELD.values())
    evidence: list[SupportingEvidence] = []
    for spec in FINANCE_PROFILE_FIELDS:
        origin = profile.origins[spec.name]
        if origin == Origin.UPSTREAM or spec.name in mapped:
            continue
        evidence.append(
            SupportingEvidence(
                field=spec.name,
                value=str(finance_profile[spec.name]),
                source="fastapi.input_contract",
                snapshotId=None,
                isDefault=origin == Origin.DEFAULT,
                isEstimated=origin == Origin.ESTIMATED,
                estimationMethod=None,
            )
        )
    return evidence


def _finance_origin_warnings(profile: ResolvedFinanceProfile) -> list[str]:
    """기본값/추정값으로 채워진 필드를 경고 코드로 드러낸다."""
    warnings = [f"FINANCE_FIELD_DEFAULTED:{name}" for name in profile.defaulted_fields]
    warnings.extend(
        f"FINANCE_FIELD_ESTIMATED:{name}" for name in profile.estimated_fields
    )
    return warnings


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
        elif warning.startswith("FINANCE_FIELD_DEFAULTED:"):
            # 기본값으로 채운 입력은 그만큼 사용자 실제 상태를 모른다는 뜻이다.
            penalties += _DEFAULTED_FIELD_PENALTY
        elif warning.startswith("FINANCE_FIELD_ESTIMATED:"):
            penalties += _ESTIMATED_FIELD_PENALTY
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

    resolved_profile, spending_estimate = _resolve_finance(request)
    finance_profile = resolved_profile.as_dict()
    current_balance = float(finance_profile["current_balance"])
    emergency_fund_balance = float(finance_profile["emergency_fund_balance"])
    expected_card_payment_amount = float(finance_profile["expected_card_payment_amount"])
    savebox_balance = float(finance_profile["savebox_balance"])
    seed_warnings.extend(_finance_origin_warnings(resolved_profile))
    seed_warnings.extend(_spending_warnings(spending_estimate))
    finance_model_signal, finance_model_state = predict_finance_signal(
        current_price=current_price,
        finance_profile=finance_profile,
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
        finance_profile=resolved_profile,
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
            isDefault=_evidence_origin(
                str(evidence.get("feature", "")), resolved_profile
            )
            == Origin.DEFAULT,
            isEstimated=(
                str(evidence.get("feature", "")) == "current_price" and price_estimated
            )
            or _evidence_origin(str(evidence.get("feature", "")), resolved_profile)
            == Origin.ESTIMATED,
            estimationMethod=("page_text_closest_numeric" if price_estimated else None),
        )
        for evidence in item.get("supporting_evidence", [])
    ]
    supporting_evidence.extend(
        _unmapped_origin_evidence(resolved_profile, finance_profile)
    )
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
