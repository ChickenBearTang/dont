"""XAI 랩: 모델을 검증하기 위해 '모델이 무엇을 보고 무엇을 했는가'를 보여주는 데이터.

운영 판단 경로(domain.xai_purchase)와 분리돼 있다. 여기서 만드는 값은 화면에 보여주기 위한
읽기 전용 요약이며 판단에는 영향을 주지 않는다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

AI_DIR = Path(__file__).resolve().parents[3]
PRICE_ARTIFACT_DIR = AI_DIR / "data" / "artifacts" / "price_retrain_model"
FINANCE_ARTIFACT_DIR = AI_DIR / "data" / "artifacts" / "finance_retrain_model"
PRICE_ROWS_PATH = AI_DIR / "data" / "price_training_rows_from_crawl.json"
SNAPSHOT_PATH = AI_DIR / "data" / "lab" / "evaluation_snapshot.json"

_TRUE = {"1", "true", "yes", "on"}


def lab_enabled() -> bool:
    """랩은 모델 내부를 보여주므로 기본은 꺼져 있다. AI_XAI_LAB_ENABLED=1 로 켠다."""
    return os.getenv("AI_XAI_LAB_ENABLED", "").strip().lower() in _TRUE


FINANCE_FEATURE_DESC: dict[str, str] = {
    "current_balance": "현재 계좌 잔액",
    "emergency_fund_balance": "비상자금 잔액",
    "savebox_balance": "세이브박스(구매 예치) 잔액",
    "expected_card_payment_amount": "이번 달 카드 결제 예정액",
    "days_until_card_due": "카드 결제일까지 남은 일수",
    "monthly_spending_30d": "최근 30일 지출 (거래 내역에서 계산)",
    "product_price": "구매하려는 상품 가격",
    "product_price_vs_monthly_spending": "가격 ÷ 월 지출 (모델 안에서 계산)",
    "projected_balance_after_purchase": "세이브박스 − 가격 = 구매 후 여유 (모델 안에서 계산)",
    "product_price_vs_emergency_fund": "가격 ÷ 비상자금 (모델 안에서 계산)",
}

GROUP_LABEL: dict[str, str] = {
    "product_price_vs_monthly_spending": "가격 부담 (월 지출 대비)",
    "projected_balance_after_purchase": "구매 후 여유 자금",
    "emergency_fund_balance": "비상자금",
    "days_until_card_due": "카드 결제 부담",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe(fn):
    try:
        return fn(), None
    except Exception as exc:  # 한 섹션이 깨져도 나머지는 보여준다
        return None, f"{type(exc).__name__}: {exc}"


def build_overview() -> dict[str, Any]:
    from ai.finance_engine.allowlist import RAW_INPUT_NAMES, SCHEMA_VERSION as FINANCE_SCHEMA, training_feature_names as finance_features
    from ai.finance_engine.explain import EXPLANATION_GROUPS
    from ai.price_engine.allowlist import SCHEMA_VERSION as PRICE_SCHEMA, training_feature_names as price_features
    from ai.validation import assess_price_artifact

    price_meta, price_err = _safe(lambda: _read_json(PRICE_ARTIFACT_DIR / "metadata.json"))
    finance_meta, finance_err = _safe(lambda: _read_json(FINANCE_ARTIFACT_DIR / "metadata.json"))

    price_model: dict[str, Any] = {
        "id": "price_model",
        "name": "가격 모델",
        "role": "현재 가격이 시장 가격 흐름에 비해 싼지 비싼지의 신호 (price_model_gap_score)",
        "family": (price_meta or {}).get("model_family", "unknown"),
        "target": (price_meta or {}).get("target_name"),
        "features": [{"name": n} for n in price_features()],
        "schema_version": PRICE_SCHEMA,
        "trained_at": (price_meta or {}).get("trained_at"),
        "train_rows": (price_meta or {}).get("train_row_count"),
        "data_source": {
            "collected_by": "크롤러(퀘이사존 핫딜 목록) → 가격 이력(Postgres) → 이력 피처 계산",
            "training_file": "data/price_training_rows_from_crawl.json",
            "label_source": "관측된 가격 (정답=current_effective_price)",
        },
        "error": price_err,
    }
    if price_meta is not None:
        verdict = assess_price_artifact(price_meta)
        price_model["trust"] = {"trusted": verdict.trusted, "reasons": verdict.reasons, "describe": verdict.describe()}
        price_model["status"] = "ok" if verdict.trusted else "blocked"
    else:
        price_model["status"] = "missing"

    finance_model: dict[str, Any] = {
        "id": "finance_model",
        "name": "재무 모델",
        "role": "구매 후 재무가 위험해지는 정도를 low/medium/high 로 분류 (finance_model_risk_score)",
        "family": (finance_meta or {}).get("model_family", "unknown"),
        "target": (finance_meta or {}).get("target_name"),
        "features": [
            {"name": n, "description": FINANCE_FEATURE_DESC.get(n, ""), "kind": "입력" if n in RAW_INPUT_NAMES else "모델 안에서 계산"}
            for n in finance_features()
        ],
        "schema_version": FINANCE_SCHEMA,
        "trained_at": (finance_meta or {}).get("trained_at"),
        "train_rows": (finance_meta or {}).get("train_row_count"),
        "metrics": {
            k: (finance_meta or {}).get(k) for k in ("accuracy_test", "macro_f1_test") if (finance_meta or {}).get(k) is not None
        },
        "data_source": {
            "collected_by": "추론 시: Spring 재무 프로필 + 최근 거래 내역 (월 지출은 거래에서 계산)",
            "training_file": "(합성) 20~30대 유형별 분포 + 균등 분포 혼합",
            "label_source": (finance_meta or {}).get("label_source", "unknown"),
            "label_rule_version": (finance_meta or {}).get("label_rule_version"),
            "training_population": (finance_meta or {}).get("training_population"),
            "persona_params_version": (finance_meta or {}).get("persona_params_version"),
        },
        "caveat": "라벨이 손으로 쓴 규칙이 붙인 합성 데이터라서 점수는 정확도가 아니라 '규칙을 얼마나 따라 하나'입니다.",
        "error": finance_err,
        "status": "synthetic" if finance_meta is not None else "missing",
    }

    nodes = [
        {"id": "request", "name": "Spring 요청", "kind": "input", "status": "ok",
         "role": "구매 요청 + 재무 프로필 + 최근 거래 내역(최대 50건)"},
        {"id": "contract", "name": "입력 계약", "kind": "gate", "status": "ok",
         "role": "필수값이 없거나 깨졌으면 422, 기본값으로 채운 값은 표시"},
        price_model,
        finance_model,
        {"id": "decision", "name": "규칙 엔진", "kind": "rule", "status": "ok",
         "role": "BUY_NOW / WAIT / REVIEW / NOT_RECOMMENDED 를 if/else 규칙으로 결정 (학습 모델이 아님)"},
        {"id": "shap", "name": "SHAP 설명", "kind": "explain", "status": "ok" if finance_meta else "missing",
         "role": "재무 모델의 실제 SHAP 을 의미 묶음 4개로 합쳐 '구매 유리/불리'로 보여줌",
         "groups": [{"id": g, "label": GROUP_LABEL.get(g, g), "members": list(m)} for g, m in EXPLANATION_GROUPS.items()]},
        {"id": "counterfactual", "name": "반사실 탐색", "kind": "explain", "status": "ok",
         "role": "가격·비상자금·세이브박스·잔액을 바꿔 보며 모델과 규칙을 다시 돌려, 확인된 변화만 제안"},
        {"id": "response", "name": "응답", "kind": "output", "status": "ok", "role": "판단·근거·제안·경고·신뢰도"},
    ]
    edges = [
        ["request", "contract"], ["contract", "price_model"], ["contract", "finance_model"],
        ["price_model", "decision"], ["finance_model", "decision"],
        ["finance_model", "shap"], ["decision", "counterfactual"], ["shap", "response"],
        ["counterfactual", "response"], ["decision", "response"],
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "nodes": nodes,
        "edges": edges,
        "flags": {
            "AI_XAI_LAB_ENABLED": lab_enabled(),
            "AI_PRICE_MODEL_ALLOW_UNTRUSTED": os.getenv("AI_PRICE_MODEL_ALLOW_UNTRUSTED", "").strip().lower() in _TRUE,
            "AI_XAI_DICE_ENABLED": os.getenv("AI_XAI_DICE_ENABLED", "").strip().lower() in _TRUE,
            "AI_XAI_SHAP_ENABLED": os.getenv("AI_XAI_SHAP_ENABLED", "1").strip().lower() in _TRUE,
        },
    }


def build_validation() -> dict[str, Any]:
    from ai.finance_engine.personas import generate_training_rows
    from ai.price_engine.allowlist import training_feature_names as price_features
    from ai.validation import (
        assess_price_artifact,
        validate_finance_rows,
        validate_price_training_rows,
        validate_training_setup,
    )

    reports: list[dict[str, Any]] = []

    rows, err = _safe(lambda: _read_json(PRICE_ROWS_PATH))
    if rows is not None:
        report = validate_price_training_rows(rows).to_dict()
        report.update(title="가격 모델 학습 데이터", source="data/price_training_rows_from_crawl.json")
        reports.append(report)
    else:
        reports.append({"name": "price_training_rows", "title": "가격 모델 학습 데이터", "ok": False, "error": err, "issues": []})

    setup = validate_training_setup(
        feature_names=list(price_features()),
        target_name="current_effective_price",
        derived_from_target=("price_vs_avg_7d", "price_vs_avg_30d", "price_to_min_30d_gap", "price_to_max_30d_gap"),
    ).to_dict()
    setup.update(title="가격 모델 학습 설정 (정답 누수)", source="price_engine/allowlist.py")
    reports.append(setup)

    finance = validate_finance_rows(generate_training_rows("mixed", row_count=3000, seed=11), check_rule=True).to_dict()
    finance.update(title="재무 모델 합성 학습 데이터 (샘플 3,000행)", source="finance_engine/personas.py")
    reports.append(finance)

    meta, _ = _safe(lambda: _read_json(PRICE_ARTIFACT_DIR / "metadata.json"))
    verdict = None
    if meta is not None:
        v = assess_price_artifact(meta)
        verdict = {"trusted": v.trusted, "reasons": v.reasons, "describe": v.describe()}
    return {"reports": reports, "price_artifact_verdict": verdict}


@lru_cache(maxsize=1)
def build_distributions() -> dict[str, Any]:
    import numpy as np

    from ai.finance_engine.personas import PERSONA_NAMES, generate_persona_rows
    from ai.finance_engine.synthetic import generate_rows

    n = 4000
    sources = {
        "uniform": generate_rows(row_count=n, seed=101),
        "persona": generate_persona_rows(row_count=n, seed=101),
    }

    def histogram(values_by_source: dict[str, list[float]], *, lo: float, hi: float, bins: int = 24) -> dict[str, Any]:
        edges = np.logspace(math.log10(lo), math.log10(hi), bins + 1)
        out: dict[str, list[float]] = {}
        for name, values in values_by_source.items():
            counts, _ = np.histogram(np.clip(values, lo, hi), bins=edges)
            out[name] = [round(float(c) / max(len(values), 1), 5) for c in counts]
        return {"edges": [round(float(e), 2) for e in edges], "share": out}

    def column(name: str) -> dict[str, list[float]]:
        return {src: [float(r[name]) for r in rows] for src, rows in sources.items()}

    emergency_months = {
        src: [float(r["emergency_fund_balance"]) / max(float(r["monthly_spending_30d"]), 1.0) for r in rows if r["emergency_fund_balance"] > 0]
        for src, rows in sources.items()
    }
    class_share = {
        src: {lab: round(sum(1 for r in rows if r["finance_risk_bucket"] == lab) / len(rows), 4) for lab in ("low", "medium", "high")}
        for src, rows in sources.items()
    }
    persona_share = {
        name: {
            lab: round(
                sum(1 for r in sources["persona"] if r["persona"] == name and r["finance_risk_bucket"] == lab)
                / max(sum(1 for r in sources["persona"] if r["persona"] == name), 1),
                4,
            )
            for lab in ("low", "medium", "high")
        }
        for name in PERSONA_NAMES
    }
    corr = {
        src: round(
            float(np.corrcoef(np.log([r["monthly_spending_30d"] for r in rows]), np.log([max(r["current_balance"], 1.0) for r in rows]))[0, 1]),
            3,
        )
        for src, rows in sources.items()
    }
    return {
        "rows_per_source": n,
        "histograms": {
            "monthly_spending_30d": {"label": "월 지출 (원, 로그 축)", **histogram(column("monthly_spending_30d"), lo=3e5, hi=1e7)},
            "current_balance": {"label": "계좌 잔액 (원, 로그 축)", **histogram(column("current_balance"), lo=3e4, hi=3e7)},
            "product_price": {"label": "상품 가격 (원, 로그 축)", **histogram(column("product_price"), lo=1e4, hi=3e6)},
            "emergency_months": {"label": "비상자금 ÷ 월 지출 (개월, 로그 축)", **histogram(emergency_months, lo=0.05, hi=30)},
        },
        "class_share": class_share,
        "persona_class_share": persona_share,
        "log_corr_monthly_vs_balance": corr,
        "note": "유형 분포의 파라미터는 가정값이다 (통계청 수치로 검증되지 않음).",
    }


def load_evaluation_snapshot() -> dict[str, Any]:
    if not SNAPSHOT_PATH.exists():
        return {
            "available": False,
            "how": "cd backend/AI_TMP && python -m ai.scripts.build_lab_snapshot",
        }
    data = _read_json(SNAPSHOT_PATH)
    data["available"] = True
    return data


_PROFILE_KEYS = (
    "current_balance", "emergency_fund_balance", "savebox_balance",
    "expected_card_payment_amount", "days_until_card_due", "monthly_spending_30d",
)


def inspect_finance(*, price: float, profile: Mapping[str, Any]) -> dict[str, Any]:
    """재무 모델이 이 입력에서 무엇을 보고 어떻게 판단했는지 (확률, 열별 SHAP, 묶음)."""
    from ai.finance_engine.explain import EXPLANATION_GROUPS, explain_model_features, group_contributions
    from ai.finance_engine.inference import (
        build_finance_inference_payload,
        load_validated_artifact,
        predict_finance_signal,
    )

    missing = [k for k in _PROFILE_KEYS if k not in profile]
    if missing:
        raise ValueError(f"missing fields: {missing}")
    clean: dict[str, float] = {}
    for key in _PROFILE_KEYS:
        value = profile[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{key} must be a finite number")
        clean[key] = max(float(value), 0.0)
    if not isinstance(price, (int, float)) or isinstance(price, bool) or not math.isfinite(float(price)) or price <= 0:
        raise ValueError("price must be a positive number")

    signal, state = predict_finance_signal(current_price=int(price), finance_profile=clean, enabled=True)
    if not state.get("enabled"):
        return {"enabled": False, "state": state}

    artifact, _, failure = load_validated_artifact(None)
    if failure is not None or artifact is None:
        return {"enabled": False, "state": failure}
    payload = build_finance_inference_payload(current_price=int(price), finance_profile=clean)
    contributions, base = explain_model_features(artifact.model, payload)

    from ai.finance_engine.features import derive_model_features

    values = derive_model_features(payload)
    groups = group_contributions(contributions)
    return {
        "enabled": True,
        "state": {k: v for k, v in state.items() if k != "artifact_path"},
        "probabilities": {k: signal[f"finance_model_{k}_prob"] for k in ("low", "medium", "high")},
        "risk_bucket": signal["finance_model_risk_bucket"],
        "risk_score": signal["finance_model_risk_score"],
        "base_margin": base,
        "high_margin": base + sum(contributions.values()),
        "features": sorted(
            (
                {
                    "name": name,
                    "description": FINANCE_FEATURE_DESC.get(name, ""),
                    "value": values[name],
                    "risk_contribution": contribution,
                }
                for name, contribution in contributions.items()
            ),
            key=lambda f: -abs(f["risk_contribution"]),
        ),
        "groups": [
            {"id": g, "label": GROUP_LABEL.get(g, g), "members": list(EXPLANATION_GROUPS[g]), "favorability": -v}
            for g, v in groups.items()
        ],
        "reference": "20~30대 유형별 합성 인구 100명 (가정값)",
    }


def simulate_purchase(req: Mapping[str, Any]) -> dict[str, Any]:
    """운영 판단 경로를 그대로 돌리되 감사 로그에는 남기지 않는다 (모의 평가).

    월 지출은 운영과 같이 거래 내역에서 계산되므로, 입력한 월 지출을 오늘 날짜의
    거래 한 건으로 만들어 넘긴다.
    """
    from datetime import date

    from domain.xai_purchase.schemas import PurchaseXaiEvaluationRequest
    from domain.xai_purchase.service import evaluate_pr_purchase_xai

    def pv(value: Any) -> dict[str, Any]:
        return {"value": value, "source": "xai-lab", "snapshotId": "lab", "isDefault": False, "isEstimated": False}

    payload = {
        "requestId": "xai-lab",
        "schemaVersion": "v1",
        "contextVersion": "v1",
        "purchase": {
            "postId": 0, "title": "XAI 랩 모의 평가", "itemName": str(req.get("item_name") or "모의 상품"),
            "content": "lab", "category": str(req.get("category") or "IT"), "purchaseUrl": None,
            "priceAmount": pv(req["price"]),
        },
        "financeProfile": {
            "currentBalance": pv(req["current_balance"]),
            "emergencyFundBalance": pv(req["emergency_fund_balance"]),
            "expectedCardPaymentAmount": pv(req["expected_card_payment_amount"]),
            "daysUntilCardDue": pv(req["days_until_card_due"]),
            "saveboxBalance": pv(req["savebox_balance"]),
        },
        "recentTransactions": [
            {
                "transactionDate": date.today().strftime("%Y%m%d"), "transactionTime": "120000",
                "merchantName": "랩", "categoryName": "기타",
                "transactionAmount": int(req["monthly_spending_30d"]),
            }
        ],
    }
    response = evaluate_pr_purchase_xai(PurchaseXaiEvaluationRequest.model_validate(payload), record_audit=False)
    return response.model_dump(by_alias=True)
