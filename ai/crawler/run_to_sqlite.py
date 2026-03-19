from __future__ import annotations

import argparse
import json

from ai.crawler.hot_deal_crawler import HotDealCrawler
from ai.storage import SqliteCrawlStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default="ai/data/crawl.db")
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--overlap-threshold", type=int, default=30)
    args = parser.parse_args()

    store = SqliteCrawlStore(db_path=args.db_path)
    crawler = HotDealCrawler()

    crawl_result = crawler.crawl_until_overlap(
        keyword=args.keyword,
        start_page=args.start_page,
        max_pages=args.max_pages,
        overlap_threshold=args.overlap_threshold,
        is_seen=store.is_seen,
    )
    save_stats = store.save_result(crawl_result)

    payload = {
        "source": crawl_result.source,
        "fetched_items": len(crawl_result.items),
        "inserted": save_stats.inserted,
        "updated": save_stats.updated,
        "db_path": args.db_path,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
