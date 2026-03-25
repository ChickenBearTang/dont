from __future__ import annotations

import argparse
import json
import os
from typing import Any

from ai.crawler.hot_deal_crawler import HotDealCrawler
from ai.finance_profile import fetch_finance_profile
from ai.manager import AIPipelineManager
from ai.models import CrawlResult
from ai.xai.analyzer import ExplainabilityAnalyzer
from ai.xai.counterfactuals import CounterfactualEngine
from ai.xai.dice_engine import DiceCounterfactualEngine
from ai.xai.shap_engine import ShapContributionEngine


def _basic_payload(result: CrawlResult) -> dict[str, Any]:
    return {
        "source": result.source,
        "item_count": len(result.items),
    }


def _resolve_finance_profile(
    *,
    finance_api_url: str | None,
    finance_api_timeout: int,
) -> dict[str, float | int] | None:
    resolved_url = finance_api_url or os.environ.get("AI_FINANCE_API_URL")
    if resolved_url is None or resolved_url.strip() == "":
        return None
    return fetch_finance_profile(
        resolved_url,
        timeout=max(finance_api_timeout, 1),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xai", action="store_true")
    parser.add_argument("--xai-top-k", type=int, default=3)
    parser.add_argument("--finance-api-url", default=None)
    parser.add_argument("--finance-api-timeout", type=int, default=3)
    args = parser.parse_args()

    crawler = HotDealCrawler(fetch=lambda _: "")
    manager: AIPipelineManager

    if not args.xai:
        manager = AIPipelineManager(crawler=crawler)
        result = manager.run()
        payload = _basic_payload(result)
        print(json.dumps(payload, ensure_ascii=True))
        return

    finance_profile = _resolve_finance_profile(
        finance_api_url=args.finance_api_url,
        finance_api_timeout=args.finance_api_timeout,
    )
    fallback_counterfactual_engine = CounterfactualEngine()
    analyzer = ExplainabilityAnalyzer(
        finance_profile=finance_profile or {},
        counterfactual_engine=fallback_counterfactual_engine,
        dice_counterfactual_engine=DiceCounterfactualEngine(
            fallback_engine=fallback_counterfactual_engine
        ),
        shap_contribution_engine=ShapContributionEngine(),
    )
    top_k = max(1, min(int(args.xai_top_k), 4))

    manager = AIPipelineManager(
        crawler=crawler,
        analyzer=lambda result: analyzer.analyze_crawl_result(result, top_k=top_k),
        analyzer_soft_fail=True,
    )
    result_payload = manager.run()
    if isinstance(result_payload, CrawlResult):
        payload = _basic_payload(result_payload)
    else:
        payload = result_payload
    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
