from __future__ import annotations

import argparse
import json
import os

from .hot_deal_crawler import HotDealCrawler
from ..storage.postgres_store import PostgresCrawlStore


def _load_env_file(env_path: str = ".env") -> None:
    if not os.path.exists(env_path):
        return

    with open(env_path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if line == "" or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            if key == "" or key in os.environ:
                continue

            parsed_value = value.strip()
            if (
                len(parsed_value) >= 2
                and parsed_value[0] == parsed_value[-1]
                and parsed_value[0] in ('"', "'")
            ):
                parsed_value = parsed_value[1:-1]
            os.environ[key] = parsed_value


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


def main() -> None:
    _load_env_file()
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", default=_default_dsn())
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=1000)
    parser.add_argument("--overlap-threshold", type=int, default=30)
    args = parser.parse_args()

    store = PostgresCrawlStore(dsn=args.db_url)
    crawler = HotDealCrawler()

    crawl_result = crawler.crawl_until_overlap(
        keyword=args.keyword,
        start_page=args.start_page,
        max_pages=args.max_pages,
        overlap_threshold=args.overlap_threshold,
        is_seen=store.is_seen,
    )
    save_stats = store.save_result(crawl_result)
    window_stats = store.read_window_stats()

    payload = {
        "source": crawl_result.source,
        "fetched_items": len(crawl_result.items),
        "inserted": save_stats.inserted,
        "updated": save_stats.updated,
        "db_backend": "postgresql",
        "price_stats": window_stats,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
