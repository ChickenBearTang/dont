from __future__ import annotations

import json

from ai.crawler.hot_deal_crawler import HotDealCrawler
from ai.manager import AIPipelineManager


def main() -> None:
    crawler = HotDealCrawler(fetch=lambda _: "")
    manager = AIPipelineManager(crawler=crawler)
    result = manager.run()
    payload = {
        "source": result.source,
        "item_count": len(result.items),
    }
    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
