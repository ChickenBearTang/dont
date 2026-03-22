from __future__ import annotations

import argparse
import json
from importlib import import_module
from typing import Any

from ai.crawler.hot_deal_crawler import HotDealCrawler
from ai.manager import AIPipelineManager
from ai.models import CrawlResult


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


class AIPipelineApplication:
    def parse_args(self, argv: list[str] | None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(prog="python -m ai")
        parser.add_argument("--xai", action="store_true", help="Enable explainability output")
        parser.add_argument(
            "--top-k",
            type=_positive_int,
            default=3,
            help="Number of explanation reasons per item (must be > 0)",
        )
        return parser.parse_args(argv)

    def build_crawler(self, args: argparse.Namespace) -> HotDealCrawler:
        del args
        return HotDealCrawler(fetch=lambda _: "")

    def build_manager(self, args: argparse.Namespace) -> AIPipelineManager:
        crawler = self.build_crawler(args)
        if not args.xai:
            return AIPipelineManager(crawler=crawler)

        analyzer_module = import_module("ai.xai.analyzer")
        analyzer = analyzer_module.ExplainabilityAnalyzer()
        return AIPipelineManager(
            crawler=crawler,
            analyzer=lambda result: analyzer.analyze_crawl_result(result, top_k=args.top_k),
        )

    def build_payload(self, result: Any, args: argparse.Namespace) -> dict[str, Any]:
        if not args.xai:
            crawl_result = result
            if not isinstance(crawl_result, CrawlResult):
                raise TypeError("Expected CrawlResult when --xai is not enabled")
            return {
                "source": crawl_result.source,
                "item_count": len(crawl_result.items),
            }

        analysis = result
        if not isinstance(analysis, dict):
            raise TypeError("Expected analyzer output dict when --xai is enabled")

        crawl_candidate = analysis.get("crawl")
        crawl: dict[str, Any] = crawl_candidate if isinstance(crawl_candidate, dict) else {}

        explanations_candidate = crawl.get("items")
        explanations: list[Any] = explanations_candidate if isinstance(explanations_candidate, list) else []

        source_candidate = crawl.get("source")
        source = source_candidate if isinstance(source_candidate, str) else ""

        return {
            "source": source,
            "item_count": len(explanations),
            "schema_version": analysis.get("schema_version"),
            "explanations": explanations,
            "analysis": analysis,
        }

    def run(self, argv: list[str] | None = None) -> int:
        args = self.parse_args(argv)
        manager = self.build_manager(args)
        result = manager.run()
        payload = self.build_payload(result, args)
        print(json.dumps(payload, ensure_ascii=True))
        return 0


def main(argv: list[str] | None = None) -> int:
    app = AIPipelineApplication()
    return app.run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
