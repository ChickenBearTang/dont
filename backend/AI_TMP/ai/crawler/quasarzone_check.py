from __future__ import annotations

import argparse
import json

import requests

TARGET_URL = "https://quasarzone.com/bbs/qb_saleinfo"
DEFAULT_KEYWORDS = ["포카리스웨트", "21,200", "/bbs/qb_saleinfo/views/"]


def fetch_response_body(url: str = TARGET_URL, timeout: int = 10) -> tuple[int, str]:
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.status_code, response.text


def check_keywords(body: str, keywords: list[str]) -> dict[str, bool]:
    return {keyword: keyword in body for keyword in keywords}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("keywords", nargs="*", default=DEFAULT_KEYWORDS)
    parser.add_argument("--url", default=TARGET_URL)
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()

    status_code, body = fetch_response_body(url=args.url, timeout=args.timeout)
    payload = {
        "url": args.url,
        "status_code": status_code,
        "body_length": len(body),
        "matches": check_keywords(body, args.keywords),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
