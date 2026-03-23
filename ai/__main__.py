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


def _default_finance_api_timeout() -> int:
    raw = os.environ.get("AI_FINANCE_API_TIMEOUT", "3")
    try:
        parsed = int(raw)
    except ValueError:
        return 3
    return parsed if parsed > 0 else 3


class AIPipelineApplication:
    def parse_args(self, argv: list[str] | None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(prog="python -m ai")
        parser.add_argument(
            "--xai",
            action="store_true",
            help=(
                "Enable Explainable AI (XAI) output with schema_version, "
                "explanations, and analysis payload fields"
            ),
        )
        parser.add_argument(
            "--top-k",
            type=_positive_int,
            default=3,
            help="Number of explanation reasons per item (must be > 0)",
        )
        parser.add_argument(
            "--real-crawl", action="store_true", help="Fetch data from real source"
        )
        parser.add_argument(
            "--persist-db",
            action="store_true",
            help="Persist crawled data into PostgreSQL",
        )
        parser.add_argument(
            "--db-url", default=_default_dsn(), help="PostgreSQL DSN for persistence"
        )
        parser.add_argument("--current-balance", type=float, default=1500000.0)
        parser.add_argument("--emergency-fund-balance", type=float, default=600000.0)
        parser.add_argument(
            "--expected-card-payment-amount", type=float, default=200000.0
        )
        parser.add_argument("--days-until-card-due", type=int, default=14)
        parser.add_argument(
            "--finance-api-url",
            default=os.environ.get("AI_FINANCE_API_URL"),
            help="Spring finance profile API URL (optional)",
        )
        parser.add_argument(
            "--finance-api-timeout",
            type=_positive_int,
            default=_default_finance_api_timeout(),
            help="Spring finance API timeout in seconds (must be > 0)",
        )
        return parser.parse_args(argv)

    def _cli_finance_profile(self, args: argparse.Namespace) -> dict[str, float | int]:
        return {
            "current_balance": args.current_balance,
            "emergency_fund_balance": args.emergency_fund_balance,
            "expected_card_payment_amount": args.expected_card_payment_amount,
            "days_until_card_due": args.days_until_card_due,
        }

    def build_finance_profile(
        self,
        args: argparse.Namespace,
    ) -> tuple[dict[str, float | int], str]:
        profile = self._cli_finance_profile(args)
        finance_api_url = args.finance_api_url
        if not isinstance(finance_api_url, str) or finance_api_url.strip() == "":
            return profile, "cli_default"

        finance_module = import_module("ai.finance_profile")
        fetched_profile = finance_module.fetch_finance_profile(
            finance_api_url,
            timeout=args.finance_api_timeout,
        )
        if not isinstance(fetched_profile, dict):
            return profile, "cli_default_fallback"

        merged = {
            "current_balance": float(
                fetched_profile.get("current_balance", profile["current_balance"])
            ),
            "emergency_fund_balance": float(
                fetched_profile.get(
                    "emergency_fund_balance",
                    profile["emergency_fund_balance"],
                )
            ),
            "expected_card_payment_amount": float(
                fetched_profile.get(
                    "expected_card_payment_amount",
                    profile["expected_card_payment_amount"],
                )
            ),
            "days_until_card_due": int(
                fetched_profile.get(
                    "days_until_card_due", profile["days_until_card_due"]
                )
            ),
        }
        return merged, "spring_api"

    def build_crawler(self, args: argparse.Namespace) -> HotDealCrawler:
        if args.real_crawl:
            return HotDealCrawler()
        return HotDealCrawler(fetch=lambda _: "")

    def build_manager(self, args: argparse.Namespace) -> AIPipelineManager:
        crawler = self.build_crawler(args)
        if not args.xai:
            return AIPipelineManager(crawler=crawler)

        analyzer_module = import_module("ai.xai.analyzer")
        finance_profile, finance_profile_source = self.build_finance_profile(args)
        analyzer = analyzer_module.ExplainabilityAnalyzer(
            finance_profile=finance_profile
        )

        store = None
        if args.persist_db:
            storage_module = import_module("ai.storage")
            store = storage_module.PostgresCrawlStore(dsn=args.db_url)

        def analyze_with_optional_persistence(result: CrawlResult) -> dict[str, Any]:
            window_stats: dict[str, dict[str, float | int | None]] | None = None
            db_save: dict[str, int] | None = None
            reason_top_k = min(args.top_k, 4)
            if store is not None:
                save_stats = store.save_result(result)
                window_stats = store.read_window_stats()
                db_save = {
                    "inserted": int(save_stats.inserted),
                    "updated": int(save_stats.updated),
                }

            analyzed = analyzer.analyze_crawl_result(
                result,
                top_k=reason_top_k,
                window_stats=window_stats,
            )
            analyzed["finance_profile_source"] = finance_profile_source
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
        crawl: dict[str, Any] = (
            crawl_candidate if isinstance(crawl_candidate, dict) else {}
        )

        explanations_candidate = crawl.get("items")
        explanations: list[Any] = (
            explanations_candidate if isinstance(explanations_candidate, list) else []
        )

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
