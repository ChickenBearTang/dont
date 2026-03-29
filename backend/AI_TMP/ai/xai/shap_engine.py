from __future__ import annotations

import os
from typing import Any


class ShapContributionEngine:
    def __init__(self) -> None:
        self._available = False
        self._shap: Any | None = None
        self._np: Any | None = None
        try:
            import numpy as np
            import shap

            self._np = np
            self._shap = shap
            self._available = True
        except ImportError:
            self._available = False

    def compute(
        self,
        feature_scores: dict[str, float],
    ) -> tuple[dict[str, float], dict[str, Any]]:
        normalized = {
            str(name): float(score)
            for name, score in feature_scores.items()
            if isinstance(name, str)
        }
        if len(normalized) == 0:
            return normalized, {
                "enabled": False,
                "backend": "fallback",
                "reason": "empty_features",
            }

        if not self._available or self._shap is None or self._np is None:
            return normalized, {
                "enabled": False,
                "backend": "fallback",
                "reason": "shap_unavailable",
            }

        try:
            np_mod = self._np
            if np_mod is None:
                return normalized, {
                    "enabled": False,
                    "backend": "fallback",
                    "reason": "shap_unavailable",
                }
            ordered_features = sorted(normalized.keys())
            row = np_mod.array(
                [[normalized[name] for name in ordered_features]],
                dtype=float,
            )
            background = np_mod.vstack(
                [
                    row,
                    np_mod.zeros_like(row),
                    row * 0.5,
                    row * 1.5,
                ]
            )
            mode = os.getenv("AI_XAI_SHAP_MODE", "fast").strip().lower()

            if mode != "exact":
                baseline = np_mod.mean(background, axis=0)
                values_row = row[0] - baseline
                contributions = {
                    feature_name: float(values_row[index])
                    for index, feature_name in enumerate(ordered_features)
                }
                return contributions, {
                    "enabled": True,
                    "backend": "shap_fast",
                    "feature_count": len(ordered_features),
                }

            def _surrogate(x: Any) -> Any:
                return np_mod.sum(x, axis=1)

            explainer = self._shap.Explainer(_surrogate, background)
            explanation = explainer(row)
            values = explanation.values
            values_row = values[0]
            contributions = {
                feature_name: float(values_row[index])
                for index, feature_name in enumerate(ordered_features)
            }
            return contributions, {
                "enabled": True,
                "backend": "shap",
                "feature_count": len(ordered_features),
            }
        except (ValueError, TypeError, RuntimeError):
            return normalized, {
                "enabled": False,
                "backend": "fallback",
                "reason": "shap_error",
            }
