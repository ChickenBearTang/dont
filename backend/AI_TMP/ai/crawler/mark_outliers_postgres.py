from __future__ import annotations

import argparse
import json
import os

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


def _parse_csv_values(raw: str) -> list[str]:
    return [value.strip() for value in raw.split(",") if value.strip()]


def main() -> None:
    _load_env_file()

    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", default=_default_dsn())
    parser.add_argument(
        "--channels",
        default="quasarzone,arca.live",
        help="Comma-separated source/channel tokens",
    )
    parser.add_argument(
        "--keywords",
        default="F87 pro,9800x3D",
        help="Comma-separated title keywords",
    )
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--iqr-multiplier", type=float, default=1.5)
    parser.add_argument("--min-group-size", type=int, default=4)
    args = parser.parse_args()

    channels = _parse_csv_values(args.channels)
    keywords = _parse_csv_values(args.keywords)
    if len(channels) == 0:
        raise SystemExit("channels must not be empty")
    if len(keywords) == 0:
        raise SystemExit("keywords must not be empty")

    store = PostgresCrawlStore(dsn=args.db_url)
    mark_result = store.mark_price_outliers(
        channels=channels,
        keywords=keywords,
        days=args.days,
        iqr_multiplier=args.iqr_multiplier,
        min_group_size=args.min_group_size,
    )

    payload = {
        "db_backend": "postgresql",
        "channels": channels,
        "keywords": keywords,
        "days": args.days,
        "iqr_multiplier": args.iqr_multiplier,
        "min_group_size": args.min_group_size,
        "reviewed_rows": mark_result.reviewed_rows,
        "marked_rows": mark_result.marked_rows,
        "scopes": [
            {
                "channel": scope.channel,
                "keyword": scope.keyword,
                "reviewed_count": scope.reviewed_count,
                "marked_count": scope.marked_count,
                "lower_bound": scope.lower_bound,
                "upper_bound": scope.upper_bound,
            }
            for scope in mark_result.scopes
        ],
        "price_stats_excluding_outliers": store.read_window_stats(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
