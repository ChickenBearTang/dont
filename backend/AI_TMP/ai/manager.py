from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from ai.crawler.base import Crawler
from ai.models import CrawlResult


class AIPipelineManager:
    def __init__(
        self,
        crawler: Crawler,
        analyzer: Callable[[CrawlResult], Any] | None = None,
        analyzer_soft_fail: bool = False,
    ) -> None:
        self.crawler = crawler
        self.analyzer = analyzer
        self.analyzer_soft_fail = analyzer_soft_fail

    def run(self) -> Any:
        crawl_result = self.crawler.crawl()
        if self.analyzer is None:
            return crawl_result
        try:
            return self.analyzer(crawl_result)
        except Exception as exc:
            if not self.analyzer_soft_fail:
                raise
            return self._build_xai_fallback(crawl_result=crawl_result, exc=exc)

    @staticmethod
    def _build_xai_fallback(
        crawl_result: CrawlResult, exc: Exception
    ) -> dict[str, Any]:
        return {
            "schema_version": "financial-purchase-copilot-xai-v1",
            "analyzer_id": "xai-manager-fallback",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": "financial-purchase-copilot-xai-model-v1",
            "crawl": {
                "source": crawl_result.source,
                "items": [
                    {
                        "item_id": item.url,
                        "decision": "REVIEW",
                        "decision_confidence": 0.0,
                        "reasons": [],
                        "supporting_evidence": [],
                        "reason_codes": [],
                        "reason_texts": [],
                        "counterfactual_conditions": [],
                        "counterfactuals": [],
                        "user_options": ["수동 검토 요청"],
                        "rule_version": "financial-purchase-copilot-xai-rules-v1",
                        "data_snapshot_id": "snapshot:error",
                        "polished_summary": "분석 오류로 요약을 생성하지 못했습니다.",
                        "errors": [
                            {
                                "code": "XAI_ANALYSIS_FAILED",
                                "message": "분석 처리에 실패했습니다",
                                "item_id": item.url,
                            }
                        ],
                    }
                    for item in crawl_result.items
                ],
            },
            "errors": [
                {
                    "code": "XAI_ANALYSIS_FAILED",
                    "message": "분석 처리에 실패했습니다",
                    "item_id": None,
                    "detail": str(exc),
                }
            ],
            "statistics": {},
            "finance_profile": {},
            "rule_version": "financial-purchase-copilot-xai-rules-v1",
            "audit_logs": [],
            "runtime_engines": {
                "shap": {
                    "enabled": False,
                    "backend": "fallback",
                    "reason": "analysis_failed",
                },
                "dice": {
                    "enabled": False,
                    "backend": "fallback",
                    "reason": "analysis_failed",
                },
            },
        }
