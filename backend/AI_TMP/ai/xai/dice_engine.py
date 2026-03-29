from __future__ import annotations

import hashlib
import random
from typing import Any


class DiceCounterfactualEngine:
    def __init__(self, *, fallback_engine: Any) -> None:
        self._fallback_engine = fallback_engine
        self._available = False
        self._dice_ml: Any | None = None
        self._pd: Any | None = None
        self._rf_cls: Any | None = None
        self._explainer: Any | None = None
        try:
            import dice_ml
            import pandas as pd
            from sklearn.ensemble import RandomForestClassifier

            self._dice_ml = dice_ml
            self._pd = pd
            self._rf_cls = RandomForestClassifier
            self._available = True
        except ImportError:
            self._available = False

    def _build_explainer(self) -> None:
        if (
            not self._available
            or self._dice_ml is None
            or self._pd is None
            or self._rf_cls is None
        ):
            return
        if self._explainer is not None:
            return

        rows: list[dict[str, float | int]] = []
        for price in (50_000.0, 150_000.0, 300_000.0, 600_000.0):
            for budget in (200_000.0, 500_000.0, 1_000_000.0, 2_000_000.0):
                for emergency in (0.0, 300_000.0, 600_000.0, 1_000_000.0):
                    safe = int((budget >= price) and (emergency >= 300_000.0))
                    rows.append(
                        {
                            "current_effective_price": price,
                            "available_budget": budget,
                            "emergency_buffer": emergency,
                            "decision_label": safe,
                        }
                    )

        train_df = self._pd.DataFrame(rows)
        continuous_features = [
            "current_effective_price",
            "available_budget",
            "emergency_buffer",
        ]
        for feature in continuous_features:
            train_df[feature] = train_df[feature].astype(float)
        model = self._rf_cls(n_estimators=32, random_state=42)
        x_train = train_df[continuous_features]
        y_train = train_df["decision_label"]
        model.fit(x_train, y_train)

        data = self._dice_ml.Data(
            dataframe=train_df,
            continuous_features=continuous_features,
            continuous_features_precision={
                "current_effective_price": 2,
                "available_budget": 2,
                "emergency_buffer": 2,
            },
            outcome_name="decision_label",
        )
        dice_model = self._dice_ml.Model(
            model=model,
            backend="sklearn",
            model_type="classifier",
        )
        self._explainer = self._dice_ml.Dice(data, dice_model, method="random")

    @staticmethod
    def _stable_seed(
        *,
        price_int: int | None,
        monthly_spending_30d: float,
        emergency_fund_balance: float,
        current_balance: float,
        days_until_card_due: int,
        expected_card_payment_amount: float,
    ) -> int:
        payload = (
            f"{price_int}|{monthly_spending_30d:.4f}|{emergency_fund_balance:.4f}|"
            f"{current_balance:.4f}|{days_until_card_due}|{expected_card_payment_amount:.4f}"
        )
        return int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8], 16)

    @staticmethod
    def _priority(variable: str) -> int:
        priorities = {
            "emergency_buffer": 0,
            "available_budget": 1,
            "current_effective_price": 2,
        }
        return priorities.get(variable, 9)

    @classmethod
    def _sort_key(cls, suggestion: dict[str, Any]) -> tuple[int, int, str]:
        raw_delta = suggestion.get("suggested_change", 0)
        try:
            delta = max(int(float(raw_delta)), 0)
        except (TypeError, ValueError):
            delta = 0
        variable = str(suggestion.get("variable", ""))
        return (delta, cls._priority(variable), variable)

    @classmethod
    def _select_deterministic(
        cls, suggestions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if len(suggestions) == 0:
            return []
        by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for suggestion in suggestions:
            variable = str(suggestion.get("variable", ""))
            action = str(suggestion.get("action", ""))
            key = (variable, action)
            previous = by_key.get(key)
            if previous is None or cls._sort_key(suggestion) < cls._sort_key(previous):
                by_key[key] = suggestion
        normalized = list(by_key.values())
        normalized.sort(key=cls._sort_key)
        return normalized[:3]

    @staticmethod
    def _to_suggestions(
        *,
        cf_row: dict[str, float],
        current_effective_price: float,
        available_budget: float,
        emergency_buffer: float,
    ) -> list[dict[str, Any]]:
        suggestions: list[dict[str, Any]] = []

        target_price = float(
            cf_row.get("current_effective_price", current_effective_price)
        )
        if target_price < current_effective_price:
            delta = int(current_effective_price - target_price)
            suggestions.append(
                {
                    "type": "dice",
                    "variable": "current_effective_price",
                    "action": "decrease",
                    "suggested_change": delta,
                    "threshold": target_price,
                    "message": f"가격을 약 {delta:,}원 낮추면 구매 판단이 개선될 수 있습니다.",
                }
            )

        target_budget = float(cf_row.get("available_budget", available_budget))
        if target_budget > available_budget:
            delta = int(target_budget - available_budget)
            suggestions.append(
                {
                    "type": "dice",
                    "variable": "available_budget",
                    "action": "increase",
                    "suggested_change": delta,
                    "threshold": target_budget,
                    "message": f"가용예산을 약 {delta:,}원 늘리면 구매 판단이 개선될 수 있습니다.",
                }
            )

        target_emergency = float(cf_row.get("emergency_buffer", emergency_buffer))
        if target_emergency > emergency_buffer:
            delta = int(target_emergency - emergency_buffer)
            suggestions.append(
                {
                    "type": "dice",
                    "variable": "emergency_buffer",
                    "action": "increase",
                    "suggested_change": delta,
                    "threshold": target_emergency,
                    "message": f"비상자금을 약 {delta:,}원 늘리면 리스크가 완화될 수 있습니다.",
                }
            )

        return suggestions

    def suggest(
        self,
        *,
        price_int: int | None,
        monthly_spending_30d: float,
        emergency_fund_balance: float,
        current_balance: float,
        days_until_card_due: int,
        expected_card_payment_amount: float,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        fallback = self._fallback_engine.suggest(
            price_int=price_int,
            monthly_spending_30d=monthly_spending_30d,
            emergency_fund_balance=emergency_fund_balance,
            current_balance=current_balance,
            days_until_card_due=days_until_card_due,
            expected_card_payment_amount=expected_card_payment_amount,
        )

        if not self._available or self._pd is None:
            return fallback, {
                "enabled": False,
                "backend": "fallback",
                "reason": "dice_unavailable",
            }

        try:
            self._build_explainer()
            if self._explainer is None:
                return fallback, {
                    "enabled": False,
                    "backend": "fallback",
                    "reason": "dice_init_failed",
                }

            current_effective_price = float(price_int) if price_int is not None else 0.0
            seed = self._stable_seed(
                price_int=price_int,
                monthly_spending_30d=monthly_spending_30d,
                emergency_fund_balance=emergency_fund_balance,
                current_balance=current_balance,
                days_until_card_due=days_until_card_due,
                expected_card_payment_amount=expected_card_payment_amount,
            )
            random.seed(seed)
            try:
                import numpy as np

                np.random.seed(seed % (2**32 - 1))
            except Exception:
                pass

            query = self._pd.DataFrame(
                [
                    {
                        "current_effective_price": current_effective_price,
                        "available_budget": float(current_balance),
                        "emergency_buffer": float(emergency_fund_balance),
                    }
                ]
            )
            result = self._explainer.generate_counterfactuals(
                query,
                total_CFs=6,
                desired_class="opposite",
            )
            examples = result.cf_examples_list
            if len(examples) == 0:
                return fallback, {
                    "enabled": False,
                    "backend": "fallback",
                    "reason": "dice_empty",
                }
            final_df = examples[0].final_cfs_df
            if final_df is None or len(final_df) == 0:
                return fallback, {
                    "enabled": False,
                    "backend": "fallback",
                    "reason": "dice_empty",
                }

            candidates: list[dict[str, Any]] = []
            for _, candidate_row in final_df.iterrows():
                row = {
                    "current_effective_price": float(
                        candidate_row["current_effective_price"]
                    ),
                    "available_budget": float(candidate_row["available_budget"]),
                    "emergency_buffer": float(candidate_row["emergency_buffer"]),
                }
                candidates.extend(
                    self._to_suggestions(
                        cf_row=row,
                        current_effective_price=current_effective_price,
                        available_budget=float(current_balance),
                        emergency_buffer=float(emergency_fund_balance),
                    )
                )

            suggestions = self._select_deterministic(candidates)
            if len(suggestions) == 0:
                return [
                    {
                        "type": "dice",
                        "variable": "current_effective_price",
                        "action": "wait_for_better_price",
                        "suggested_change": 0,
                        "threshold": current_effective_price,
                        "message": "DiCE 결과 기준으로 현재 조건에선 큰 변화가 없어 가격/예산 변동 시 재평가를 권장합니다.",
                    }
                ], {
                    "enabled": True,
                    "backend": "dice_ml",
                    "count": 1,
                    "reason": "dice_no_change",
                }
            return suggestions[:3], {
                "enabled": True,
                "backend": "dice_ml",
                "count": len(suggestions[:3]),
            }
        except (TypeError, ValueError, RuntimeError, IndexError):
            return fallback, {
                "enabled": False,
                "backend": "fallback",
                "reason": "dice_error",
            }
