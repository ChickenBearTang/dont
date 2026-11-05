from __future__ import annotations

import argparse
import json
from typing import Any

from ai.crawler.hot_deal_crawler import HotDealCrawler
from ai.manager import AIPipelineManager
from ai.models import CrawlResult
from ai.xai.analyzer import ExplainabilityAnalyzer
from ai.xai.counterfactuals import CounterfactualEngine
from ai.xai.dice_engine import DiceCounterfactualEngine


def _basic_payload(result: CrawlResult) -> dict[str, Any]:
    return {
        "source": result.source,
        "item_count": len(result.items),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xai", action="store_true")
    parser.add_argument("--xai-top-k", type=int, default=3)
    args = parser.parse_args()

    crawler = HotDealCrawler(fetch=lambda _: "")
    manager: AIPipelineManager

    if not args.xai:
        manager = AIPipelineManager(crawler=crawler)
        result = manager.run()
        payload = _basic_payload(result)
        print(json.dumps(payload, ensure_ascii=True))
        return

    fallback_counterfactual_engine = CounterfactualEngine()
    analyzer = ExplainabilityAnalyzer(
        finance_profile={},  # 이 CLI 는 크롤 결과 설명 시연용이다. 사용자 재무 입력은 Spring 요청(/api/v1/xai/purchase-evaluations)으로만 받는다.
        counterfactual_engine=fallback_counterfactual_engine,
        dice_counterfactual_engine=DiceCounterfactualEngine(
            fallback_engine=fallback_counterfactual_engine
        ),
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
