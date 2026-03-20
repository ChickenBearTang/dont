from __future__ import annotations

import json
from typing import List, Tuple, Dict, Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
import lightgbm as lgb
import shap

import dice_ml
from dice_ml import Dice

SEED = 42
rng = np.random.default_rng(SEED)


def make_price_data(n: int = 1500) -> pd.DataFrame:
    brands = ["Apple", "Samsung", "Sony", "LG"]
    categories = ["earbuds", "tablet", "watch"]
    sellers = ["official_mall", "open_market", "reseller"]
    options = ["basic", "pro", "max"]

    rows = []
    for _ in range(n):
        brand = rng.choice(brands)
        category = rng.choice(categories)
        seller = rng.choice(sellers)
        option = rng.choice(options)

        avg_price_30d = rng.uniform(100_000, 600_000)
        current_price = avg_price_30d * rng.uniform(0.82, 1.18)
        avg_price_7d = avg_price_30d * rng.uniform(0.94, 1.06)
        min_price_30d = avg_price_30d * rng.uniform(0.75, 0.95)
        max_price_30d = avg_price_30d * rng.uniform(1.05, 1.30)

        coupon_applied = int(rng.integers(0, 2))
        card_discount_applied = int(rng.integers(0, 2))
        shipping_fee = int(rng.choice([0, 2500, 3000, 5000]))
        inventory_status = rng.choice(
            ["in_stock", "low_stock", "out_of_stock"],
            p=[0.75, 0.20, 0.05],
        )

        effective_price = (
            current_price
            - (coupon_applied * 12000)
            - (card_discount_applied * 8000)
            + shipping_fee
        )
        ratio = effective_price / avg_price_30d

        if ratio < 0.93:
            label = "cheap"
        elif ratio > 1.06:
            label = "expensive"
        else:
            label = "normal"

        rows.append(
            {
                "brand": brand,
                "category": category,
                "seller_type": seller,
                "option_name": option,
                "current_price": round(current_price, 2),
                "avg_price_7d": round(avg_price_7d, 2),
                "avg_price_30d": round(avg_price_30d, 2),
                "min_price_30d": round(min_price_30d, 2),
                "max_price_30d": round(max_price_30d, 2),
                "coupon_applied": coupon_applied,
                "card_discount_applied": card_discount_applied,
                "shipping_fee": shipping_fee,
                "inventory_status": inventory_status,
                "label_price_bucket": label,
            }
        )
    return pd.DataFrame(rows)


def make_finance_data(n: int = 1500) -> pd.DataFrame:
    trends = ["increase", "stable", "decrease"]
    label_map = {"low": 0, "medium": 1, "high": 2}

    rows = []
    for _ in range(n):
        monthly_total_spending = rng.uniform(800_000, 4_500_000)
        monthly_fixed_spending = monthly_total_spending * rng.uniform(0.35, 0.7)
        monthly_variable_spending = monthly_total_spending - monthly_fixed_spending
        recent_30d_spending_growth_rate = rng.uniform(-0.10, 0.35)
        recent_90d_spending_trend = rng.choice(trends, p=[0.35, 0.45, 0.20])

        current_balance = rng.uniform(100_000, 3_000_000)
        emergency_fund_balance = rng.uniform(0, 3_500_000)
        debt_balance = rng.uniform(0, 1_500_000)
        expected_card_payment_amount = rng.uniform(0, 1_000_000)
        days_until_card_due = int(rng.integers(1, 30))
        avg_monthly_income = monthly_total_spending * rng.uniform(0.9, 1.8)

        product_price = rng.uniform(100_000, 600_000)
        product_price_vs_monthly_spending = product_price / monthly_total_spending
        product_price_vs_balance = product_price / max(current_balance, 1)
        projected_balance_after_purchase = current_balance - product_price
        product_price_vs_emergency_fund = product_price / max(emergency_fund_balance, 1)
        category_purchase_count_90d = int(rng.integers(0, 5))
        non_essential_flag = int(rng.integers(0, 2))

        risk_score = 0.0
        if product_price_vs_monthly_spending > 0.28:
            risk_score += 1.0
        if emergency_fund_balance < monthly_total_spending * 0.5:
            risk_score += 1.0
        if recent_30d_spending_growth_rate > 0.12:
            risk_score += 1.0
        if projected_balance_after_purchase < monthly_total_spending * 0.15:
            risk_score += 1.0
        if (
            days_until_card_due < 7
            and expected_card_payment_amount > current_balance * 0.4
        ):
            risk_score += 1.0
        if non_essential_flag == 1:
            risk_score += 0.5

        if risk_score >= 3:
            label = "high"
        elif risk_score >= 1.5:
            label = "medium"
        else:
            label = "low"

        rows.append(
            {
                "monthly_total_spending": round(monthly_total_spending, 2),
                "monthly_fixed_spending": round(monthly_fixed_spending, 2),
                "monthly_variable_spending": round(monthly_variable_spending, 2),
                "recent_30d_spending_growth_rate": round(
                    recent_30d_spending_growth_rate, 4
                ),
                "recent_90d_spending_trend": recent_90d_spending_trend,
                "current_balance": round(current_balance, 2),
                "emergency_fund_balance": round(emergency_fund_balance, 2),
                "debt_balance": round(debt_balance, 2),
                "expected_card_payment_amount": round(expected_card_payment_amount, 2),
                "days_until_card_due": days_until_card_due,
                "avg_monthly_income": round(avg_monthly_income, 2),
                "product_price": round(product_price, 2),
                "product_price_vs_monthly_spending": round(
                    product_price_vs_monthly_spending, 4
                ),
                "product_price_vs_balance": round(product_price_vs_balance, 4),
                "projected_balance_after_purchase": round(
                    projected_balance_after_purchase, 2
                ),
                "product_price_vs_emergency_fund": round(
                    product_price_vs_emergency_fund, 4
                ),
                "category_purchase_count_90d": category_purchase_count_90d,
                "non_essential_flag": non_essential_flag,
                "label_finance_risk_bucket": label,
                "label_finance_risk_int": label_map[label],
            }
        )
    return pd.DataFrame(rows)



# 가격 모델 학습
def train_price_model(
    df: pd.DataFrame,
) -> Tuple[CatBoostClassifier, List[str], List[str]]:
    feature_cols = [
        "brand",
        "category",
        "seller_type",
        "option_name",
        "current_price",
        "avg_price_7d",
        "avg_price_30d",
        "min_price_30d",
        "max_price_30d",
        "coupon_applied",
        "card_discount_applied",
        "shipping_fee",
        "inventory_status",
    ]
    cat_cols = ["brand", "category", "seller_type", "option_name", "inventory_status"]

    X = df[feature_cols]
    y = df["label_price_bucket"]

    model = CatBoostClassifier(
        loss_function="MultiClass",
        depth=6,
        learning_rate=0.07,
        iterations=120,
        random_seed=SEED,
        verbose=False,
    )
    cat_idx = [feature_cols.index(c) for c in cat_cols]
    model.fit(X, y, cat_features=cat_idx)
    return model, feature_cols, cat_cols


# 재무 모델 학습
def train_finance_model(
    df: pd.DataFrame,
) -> Tuple[lgb.LGBMClassifier, List[str], List[str]]:
    feature_cols = [
        "monthly_total_spending",
        "monthly_fixed_spending",
        "monthly_variable_spending",
        "recent_30d_spending_growth_rate",
        "recent_90d_spending_trend",
        "current_balance",
        "emergency_fund_balance",
        "debt_balance",
        "expected_card_payment_amount",
        "days_until_card_due",
        "avg_monthly_income",
        "product_price",
        "product_price_vs_monthly_spending",
        "product_price_vs_balance",
        "projected_balance_after_purchase",
        "product_price_vs_emergency_fund",
        "category_purchase_count_90d",
        "non_essential_flag",
    ]
    cat_cols = ["recent_90d_spending_trend"]

    X = df[feature_cols].copy()
    for c in cat_cols:
        X[c] = X[c].astype("category")
    y = df["label_finance_risk_bucket"]

    model = lgb.LGBMClassifier(
        n_estimators=150,
        learning_rate=0.07,
        num_leaves=31,
        random_state=SEED,
        force_col_wise=True,
        verbose=-1,
    )
    model.fit(X, y, categorical_feature=cat_cols)
    return model, feature_cols, cat_cols


# DiCE를 위한 재무 모델 학습
def train_finance_model_for_dice(
    df: pd.DataFrame,
) -> Tuple[lgb.LGBMClassifier, List[str]]:
    # DiCE 호환성을 위해 numeric-only 모델 사용
    feature_cols = [
        "monthly_total_spending",
        "monthly_fixed_spending",
        "monthly_variable_spending",
        "recent_30d_spending_growth_rate",
        "current_balance",
        "emergency_fund_balance",
        "debt_balance",
        "expected_card_payment_amount",
        "days_until_card_due",
        "avg_monthly_income",
        "product_price",
        "product_price_vs_monthly_spending",
        "product_price_vs_balance",
        "projected_balance_after_purchase",
        "product_price_vs_emergency_fund",
        "category_purchase_count_90d",
        "non_essential_flag",
    ]
    X = df[feature_cols].copy()
    y = df["label_finance_risk_int"]

    model = lgb.LGBMClassifier(
        n_estimators=150,
        learning_rate=0.07,
        num_leaves=31,
        random_state=SEED,
        force_col_wise=True,
        verbose=-1,
    )
    model.fit(X, y)
    return model, feature_cols


def apply_decision_rule(
    price_bucket: str,
    expected_drop_prob: float,
    finance_risk_bucket: str,
    affordability_score: float,
) -> str:
    if finance_risk_bucket == "high":
        return "HOLD"
    elif (
        price_bucket == "cheap"
        and finance_risk_bucket == "low"
        and affordability_score >= 0.55
    ):
        return "BUY_NOW"

    wait_threshold = 0.45 if affordability_score < 0.4 else 0.6
    if expected_drop_prob >= wait_threshold:
        return "WAIT"
    else:
        return "REVIEW"


REASON_CODE_MAP = {
    "avg_price_30d": ("PRICE_RELATIVE_TO_30D_AVG", "price_shap"),
    "current_price": ("CURRENT_PRICE_LEVEL", "price_shap"),
    "coupon_applied": ("COUPON_DISCOUNT_APPLIED", "price_shap"),
    "shipping_fee": ("SHIPPING_COST_REDUCES_ATTRACTIVENESS", "price_shap"),
    "recent_30d_spending_growth_rate": ("RECENT_SPENDING_SURGE", "finance_shap"),
    "emergency_fund_balance": ("EMERGENCY_FUND_TOO_LOW", "finance_shap"),
    "projected_balance_after_purchase": (
        "BALANCE_AFTER_PURCHASE_TOO_LOW",
        "finance_shap",
    ),
    "product_price_vs_monthly_spending": (
        "PRICE_TOO_LARGE_VS_MONTHLY_SPENDING",
        "finance_shap",
    ),
    "days_until_card_due": ("CARD_DUE_SOON", "finance_shap"),
}

REASON_TEXT = {
    "PRICE_RELATIVE_TO_30D_AVG": "현재 가격이 최근 30일 평균과 비교해 유리하게 작용했습니다.",
    "CURRENT_PRICE_LEVEL": "현재 절대 가격 수준이 판단에 영향을 주었습니다.",
    "COUPON_DISCOUNT_APPLIED": "쿠폰 적용으로 실구매가가 낮아졌습니다.",
    "SHIPPING_COST_REDUCES_ATTRACTIVENESS": "배송비가 가격 매력도를 일부 낮췄습니다.",
    "RECENT_SPENDING_SURGE": "최근 소비 증가로 재무 부담 가능성이 있습니다.",
    "EMERGENCY_FUND_TOO_LOW": "비상자금이 권장 수준보다 낮습니다.",
    "BALANCE_AFTER_PURCHASE_TOO_LOW": "구매 후 잔액이 너무 낮아질 수 있습니다.",
    "PRICE_TOO_LARGE_VS_MONTHLY_SPENDING": "상품 가격이 월 지출 대비 큰 편입니다.",
    "CARD_DUE_SOON": "카드 결제일이 가까워 현금흐름 부담이 있습니다.",
}


def extract_top_reasons_from_shap(
    shap_values_1d, feature_names: List[str], top_k: int = 3
) -> List[Dict[str, Any]]:
    vals = np.array(shap_values_1d).reshape(-1)
    pairs = list(zip(feature_names, vals))
    pairs = sorted(pairs, key=lambda x: abs(float(x[1])), reverse=True)[:top_k]

    reasons = []
    for feature, shap_value in pairs:
        if feature in REASON_CODE_MAP:
            code, source = REASON_CODE_MAP[feature]
            reasons.append(
                {
                    "feature": feature,
                    "shap_value": float(shap_value),
                    "reason_code": code,
                    "reason_text": REASON_TEXT[code],
                    "source_type": source,
                }
            )
    return reasons


def build_dice_from_finance_training(
    df_train: pd.DataFrame,
    model_for_dice,
    feature_cols: List[str],
):
    dice_data = dice_ml.Data(
        dataframe=df_train[feature_cols + ["label_finance_risk_int"]],
        continuous_features=feature_cols,
        outcome_name="label_finance_risk_int",
    )
    dice_model = dice_ml.Model(
        model=model_for_dice,
        backend="sklearn",
        model_type="classifier",
    )
    return Dice(dice_data, dice_model, method="genetic")


def get_desired_finance_class(current_class: str) -> int:
    if current_class == "high":
    elif current_class == "medium":
        return 0
    else:
        return 0


def build_counterfactual_fallback(finance_row: pd.DataFrame) -> List[Dict[str, Any]]:
    row = finance_row.iloc[0]
    suggestions = []

    monthly_spending = float(row["monthly_total_spending"])
    current_balance = float(row["current_balance"])
    emergency_fund = float(row["emergency_fund_balance"])
    expected_card_payment = float(row["expected_card_payment_amount"])
    days_until_due = int(row["days_until_card_due"])
    product_price = float(row["product_price"])
    spending_growth = float(row["recent_30d_spending_growth_rate"])

    if emergency_fund < monthly_spending * 0.5:
        target = round(monthly_spending * 0.5, 2)
        suggestions.append(
            {
                "type": "fallback_counterfactual",
                "message": f"비상자금을 약 {int(target - emergency_fund):,}원 더 확보하면 재무 위험이 완화될 수 있습니다.",
            }
        )

    projected_balance = current_balance - product_price
    min_safe_balance = monthly_spending * 0.15
    if projected_balance < min_safe_balance:
        gap = int(min_safe_balance - projected_balance)
        suggestions.append(
            {
                "type": "fallback_counterfactual",
                "message": f"구매 후 잔액이 너무 낮아지므로, 현재 잔액이 약 {gap:,}원 더 높거나 상품 가격이 더 낮으면 판단이 완화될 수 있습니다.",
            }
        )

    if days_until_due < 7 and expected_card_payment > current_balance * 0.4:
        suggestions.append(
            {
                "type": "fallback_counterfactual",
                "message": "카드 결제일 이후로 구매 시점을 미루면 현금흐름 부담이 완화될 수 있습니다.",
            }
        )

    if spending_growth > 0.12:
        suggestions.append(
            {
                "type": "fallback_counterfactual",
                "message": "최근 비필수 소비 증가가 완화되면 재무 판단이 더 긍정적으로 바뀔 수 있습니다.",
            }
        )

    if len(suggestions) == 0:
        suggestions.append(
            {
                "type": "fallback_counterfactual",
                "message": "가격이 더 낮아지거나 가용 잔액이 높아지면 추천이 달라질 수 있습니다.",
            }
        )

    return suggestions[:3]


def generate_counterfactuals(
    dice_exp,
    query_df: pd.DataFrame,
    desired_class: int,
    finance_row_original: pd.DataFrame,
):
    try:
        cfs = dice_exp.generate_counterfactuals(
            query_df,
            total_CFs=5,
            desired_class=desired_class,
            features_to_vary=[
                "current_balance",
                "emergency_fund_balance",
                "product_price",
                "recent_30d_spending_growth_rate",
                "expected_card_payment_amount",
                "days_until_card_due",
            ],
            permitted_range={
                "current_balance": [
                    float(query_df["current_balance"].iloc[0]),
                    2_000_000,
                ],
                "emergency_fund_balance": [
                    float(query_df["emergency_fund_balance"].iloc[0]),
                    3_000_000,
                ],
                "product_price": [200_000, float(query_df["product_price"].iloc[0])],
                "recent_30d_spending_growth_rate": [
                    -0.05,
                    float(query_df["recent_30d_spending_growth_rate"].iloc[0]),
                ],
                "expected_card_payment_amount": [
                    0,
                    float(query_df["expected_card_payment_amount"].iloc[0]),
                ],
                "days_until_card_due": [
                    int(query_df["days_until_card_due"].iloc[0]),
                    30,
                ],
            },
        )

        cf_df = cfs.cf_examples_list[0].final_cfs_df
        if cf_df is None or len(cf_df) == 0:
            return build_counterfactual_fallback(finance_row_original)

        return json.loads(cf_df.to_json(orient="records", force_ascii=False))

    except Exception:
        return build_counterfactual_fallback(finance_row_original)


def main():
    price_df = make_price_data()
    finance_df = make_finance_data()

    price_model, price_features, _ = train_price_model(price_df)
    finance_model, finance_features, _ = train_finance_model(finance_df)
    finance_model_for_dice, finance_dice_features = train_finance_model_for_dice(
        finance_df
    )

    # sample request
    price_row = pd.DataFrame(
        [
            {
                "brand": "Apple",
                "category": "earbuds",
                "seller_type": "official_mall",
                "option_name": "pro",
                "current_price": 329000,
                "avg_price_7d": 344000,
                "avg_price_30d": 349000,
                "min_price_30d": 319000,
                "max_price_30d": 389000,
                "coupon_applied": 1,
                "card_discount_applied": 0,
                "shipping_fee": 2500,
                "inventory_status": "low_stock",
            }
        ]
    )

    finance_row = pd.DataFrame(
        [
            {
                "monthly_total_spending": 2100000,
                "monthly_fixed_spending": 1200000,
                "monthly_variable_spending": 900000,
                "recent_30d_spending_growth_rate": 0.18,
                "recent_90d_spending_trend": "increase",
                "current_balance": 400000,
                "emergency_fund_balance": 500000,
                "debt_balance": 0,
                "expected_card_payment_amount": 320000,
                "days_until_card_due": 5,
                "avg_monthly_income": 2800000,
                "product_price": 329000,
                "product_price_vs_monthly_spending": round(329000 / 2100000, 4),
                "product_price_vs_balance": round(329000 / 400000, 4),
                "projected_balance_after_purchase": 400000 - 329000,
                "product_price_vs_emergency_fund": round(329000 / 500000, 4),
                "category_purchase_count_90d": 1,
                "non_essential_flag": 1,
            }
        ]
    )

    finance_row_for_model = finance_row.copy()
    finance_row_for_model["recent_90d_spending_trend"] = pd.Categorical(
        finance_row_for_model["recent_90d_spending_trend"],
        categories=["increase", "stable", "decrease"],
    )

    price_bucket = str(price_model.predict(price_row).flatten()[0])
    price_proba = price_model.predict_proba(price_row)[0]
    cheap_idx = list(price_model.classes_).index("cheap")
    expected_drop_prob = max(0.0, 1.0 - float(price_proba[cheap_idx]))
    fair_price = float(price_row["avg_price_30d"].iloc[0] * 0.96)

    finance_bucket = str(finance_model.predict(finance_row_for_model)[0])
    finance_proba = finance_model.predict_proba(finance_row_for_model)[0]
    low_idx = list(finance_model.classes_).index("low")
    affordability_score = float(finance_proba[low_idx])
    stress_score = float(1 - affordability_score)

    decision_code = apply_decision_rule(
        price_bucket=price_bucket,
        expected_drop_prob=float(expected_drop_prob),
        finance_risk_bucket=finance_bucket,
        affordability_score=float(affordability_score),
    )

    price_explainer = shap.TreeExplainer(price_model)
    price_shap_values = price_explainer.shap_values(price_row)

    if isinstance(price_shap_values, list):
        price_class_idx = list(price_model.classes_).index("cheap")
        price_shap_1d = price_shap_values[price_class_idx][0]
    else:
        price_class_idx = list(price_model.classes_).index("cheap")
        price_shap_1d = price_shap_values[0, :, price_class_idx]

    price_reasons = extract_top_reasons_from_shap(
        price_shap_1d,
        price_features,
        top_k=3,
    )

    finance_explainer = shap.TreeExplainer(finance_model)
    finance_shap_values = finance_explainer.shap_values(finance_row_for_model)

    finance_classes = list(finance_model.classes_)
    target_class = (
        "high"
        if decision_code == "HOLD" and "high" in finance_classes
        else finance_bucket
    )
    target_idx = finance_classes.index(target_class)

    if isinstance(finance_shap_values, list):
        finance_shap_1d = finance_shap_values[target_idx][0]
    else:
        finance_shap_1d = finance_shap_values[0, :, target_idx]

    finance_reasons = extract_top_reasons_from_shap(
        finance_shap_1d,
        finance_features,
        top_k=3,
    )

    dice_exp = build_dice_from_finance_training(
        finance_df,
        finance_model_for_dice,
        finance_dice_features,
    )

    finance_row_for_dice: pd.DataFrame = finance_row.loc[
        :, finance_dice_features
    ].copy()
    desired_class = get_desired_finance_class(finance_bucket)
    counterfactuals = generate_counterfactuals(
        dice_exp,
        finance_row_for_dice,
        desired_class=desired_class,
        finance_row_original=finance_row,
    )

    payload = {
        "decision": decision_code,
        "price_engine": {
            "price_bucket": price_bucket,
            "fair_price": round(fair_price, 2),
            "expected_drop_prob": round(expected_drop_prob, 4),
        },
        "finance_engine": {
            "finance_risk_bucket": finance_bucket,
            "affordability_score": round(affordability_score, 4),
            "stress_score": round(stress_score, 4),
        },
        "reasons": price_reasons + finance_reasons,
        "counterfactuals": counterfactuals,
    }

    print("=" * 80)
    print("XAI PURCHASE RECOMMENDATION DEMO")
    print("=" * 80)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
