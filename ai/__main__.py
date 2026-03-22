from __future__ import annotations

import argparse
import json
from importlib import import_module
import os
from typing import Any

from ai.crawler.hot_deal_crawler import HotDealCrawler
from ai.manager import AIPipelineManager
from ai.models import CrawlResult


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def _default_dsn() -> str:
    env_dsn = os.environ.get("AI_POSTGRES_DSN")
    if env_dsn:
        return env_dsn
    host = os.environ.get("AI_POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("AI_POSTGRES_PORT", "55432")
    db = os.environ.get("AI_POSTGRES_DB", "ai_crawl")
    user = os.environ.get("AI_POSTGRES_USER", "ai_user")
    password = os.environ.get("AI_POSTGRES_PASSWORD", "ai_password")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


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
        parser.add_argument("--real-crawl", action="store_true", help="Fetch data from real source")
        parser.add_argument("--persist-db", action="store_true", help="Persist crawled data into PostgreSQL")
        parser.add_argument("--db-url", default=_default_dsn(), help="PostgreSQL DSN for persistence")
        parser.add_argument("--current-balance", type=float, default=1500000.0)
        parser.add_argument("--emergency-fund-balance", type=float, default=600000.0)
        parser.add_argument("--expected-card-payment-amount", type=float, default=200000.0)
        parser.add_argument("--days-until-card-due", type=int, default=14)
        return parser.parse_args(argv)

    def build_crawler(self, args: argparse.Namespace) -> HotDealCrawler:
        if args.real_crawl:
            return HotDealCrawler()
        return HotDealCrawler(fetch=lambda _: "")

    def build_manager(self, args: argparse.Namespace) -> AIPipelineManager:
        crawler = self.build_crawler(args)
        if not args.xai:
            return AIPipelineManager(crawler=crawler)

        analyzer_module = import_module("ai.xai.analyzer")
        finance_profile = {
            "current_balance": args.current_balance,
            "emergency_fund_balance": args.emergency_fund_balance,
            "expected_card_payment_amount": args.expected_card_payment_amount,
            "days_until_card_due": args.days_until_card_due,
        }
        analyzer = analyzer_module.ExplainabilityAnalyzer(finance_profile=finance_profile)

        store = None
        if args.persist_db:
            storage_module = import_module("ai.storage")
            store = storage_module.PostgresCrawlStore(dsn=args.db_url)

        def analyze_with_optional_persistence(result: CrawlResult) -> dict[str, Any]:
            window_stats: dict[str, dict[str, float | int | None]] | None = None
            db_save: dict[str, int] | None = None
            if store is not None:
                save_stats = store.save_result(result)
                window_stats = store.read_window_stats()
                db_save = {
                    "inserted": int(save_stats.inserted),
                    "updated": int(save_stats.updated),
                }

            analyzed = analyzer.analyze_crawl_result(result, top_k=args.top_k, window_stats=window_stats)
            if db_save is not None:
                analyzed["db_save"] = db_save
            return analyzed

        return AIPipelineManager(
            crawler=crawler,
            analyzer=analyze_with_optional_persistence,
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
