from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from ai.models import CrawlResult
from .types import AnalysisError, CrawlExplanation, ExplainabilityResult, ItemExplanation


class ExplainabilityAnalyzer:
    ANALYZER_ID = "xai-explainability"
    MODEL_VERSION = "rules-v1"

    def __init__(
        self,
        *,
        feature_extractor: Any | None = None,
        reasoning_engine: Any | None = None,
    ) -> None:
        features_module = import_module("ai.xai.features")
        reasoning_module = import_module("ai.xai.reasoning")
        self._feature_extractor = feature_extractor or features_module.FeatureExtractor()
        self._reasoning_engine = reasoning_engine or reasoning_module.ReasoningEngine()

    def analyze_crawl_result(self, result: CrawlResult, top_k: int = 3) -> dict[str, Any]:
        sorted_items = sorted(result.items, key=lambda deal: (deal.url, deal.title))

        item_explanations: list[ItemExplanation] = []
        errors: list[AnalysisError] = []

        for deal in sorted_items:
            item_error: AnalysisError | None = None
            reasons: list[dict[str, Any]] = []

            try:
                features = self._feature_extractor.extract_features(deal)
                feature_scores = self._build_feature_scores(features)
                reasons = self._reasoning_engine.analyze(feature_scores, top_k=top_k)
            except Exception as exc:
                item_error = self._build_error(exc=exc, item_id=deal.url)
                errors.append(item_error)

            item_explanations.append(
                ItemExplanation(
                    item_id=deal.url,
                    reasons=reasons,
                    errors=[item_error] if item_error is not None else [],
                )
            )

        explainability_result = ExplainabilityResult(
            analyzer_id=self.ANALYZER_ID,
            generated_at=datetime.now(timezone.utc),
            model_version=self.MODEL_VERSION,
            crawl=CrawlExplanation(source=result.source, items=item_explanations),
            errors=errors,
        )
        return explainability_result.to_dict()

    def _build_feature_scores(self, features: dict[str, Any]) -> dict[str, float]:
        missing_fields = features.get("missing_fields", [])
        if not isinstance(missing_fields, list):
            raise ValueError("missing_fields must be a list")
        if len(missing_fields) > 0:
            missing = ",".join(str(field) for field in sorted(missing_fields))
            raise ValueError(f"deal missing required fields: {missing}")

        title_len_raw = features.get("title_len", 0)
        title_len = int(title_len_raw) if isinstance(title_len_raw, int) else 0
        title_len_score = min(title_len / 100.0, 1.0)

        has_price = bool(features.get("has_price", False))
        has_title = bool(features.get("has_title", False))

        price_raw = features.get("price_int")
        price_int = int(price_raw) if isinstance(price_raw, int) else 0
        current_price_score = 1.0 / (1.0 + (price_int / 100_000.0)) if price_int > 0 else 0.0

        return {
            "current_price": current_price_score,
            "coupon_applied": 1.0 if has_price else -1.0,
            "avg_price_30d": title_len_score,
            "shipping_fee": -float(len(missing_fields)),
            "product_price_vs_monthly_spending": 0.5 if has_title else -0.5,
        }

    def _build_error(self, *, exc: Exception, item_id: str) -> AnalysisError:
        if isinstance(exc, ValueError):
            code = "XAI_ITEM_VALIDATION_FAILED"
            message = "항목 검증에 실패했습니다"
        else:
            code = "XAI_ANALYSIS_FAILED"
            message = "분석 처리에 실패했습니다"
        return AnalysisError(code=code, message=message, item_id=item_id)
