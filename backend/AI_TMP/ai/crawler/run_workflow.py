from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from ..storage import PostgresCrawlStore


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


def _default_db_url() -> str:
    env_dsn = os.environ.get("AI_POSTGRES_DSN")
    if env_dsn:
        return env_dsn
    host = os.environ.get("AI_POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("AI_POSTGRES_PORT", "55432")
    db = os.environ.get("AI_POSTGRES_DB", "ai_crawl")
    user = os.environ.get("AI_POSTGRES_USER", "ai_user")
    password = os.environ.get("AI_POSTGRES_PASSWORD", "ai_password")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def _resolve_db_url(db_url: str | None) -> str:
    if db_url:
        return db_url
    _load_env_file()
    return _default_db_url()


def run_tests() -> dict[str, object]:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "ai/tests", "-v"]
    result = subprocess.run(command, capture_output=True, text=True)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_crawl(
    db_path: str,
    keyword: str | None,
    start_page: int,
    max_pages: int,
    overlap_threshold: int,
    backend: str = "postgres",
    db_url: str | None = None,
) -> dict[str, object]:
    if backend != "postgres":
        raise ValueError(f"Unsupported backend: {backend}")
    resolved_db_url = _resolve_db_url(db_url)
    command = [
        sys.executable,
        "-m",
        "ai.crawler.run_to_postgres",
        "--db-url",
        resolved_db_url,
        "--start-page",
        str(start_page),
        "--max-pages",
        str(max_pages),
        "--overlap-threshold",
        str(overlap_threshold),
    ]

    if keyword:
        command.extend(["--keyword", keyword])

    result = subprocess.run(command, capture_output=True, text=True)
    parsed_output: dict[str, object] | None = None
    parse_error: str | None = None
    if result.stdout.strip():
        try:
            parsed_output = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            parse_error = str(exc)

    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "parsed_output": parsed_output,
        "parse_error": parse_error,
    }


def read_samples(
    db_path: str,
    sample_limit: int,
    backend: str = "postgres",
    db_url: str | None = None,
) -> dict[str, object]:
    if backend != "postgres":
        raise ValueError(f"Unsupported backend: {backend}")
    store = PostgresCrawlStore(dsn=_resolve_db_url(db_url))
    sample_result = store.read_samples(sample_limit=sample_limit)
    return {
        "total_count": sample_result.total_count,
        "sample_items": sample_result.sample_items,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default="ai/data/crawl.db")
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--backend", choices=["postgres"], default="postgres")
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=1000)
    parser.add_argument("--overlap-threshold", type=int, default=20)
    parser.add_argument("--sample-limit", type=int, default=10)
    args = parser.parse_args()

    test_result = run_tests()
    if test_result["returncode"] != 0:
        print(json.dumps({"test_result": test_result}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    crawl_result = run_crawl(
        db_path=args.db_path,
        keyword=args.keyword,
        start_page=args.start_page,
        max_pages=args.max_pages,
        overlap_threshold=args.overlap_threshold,
        backend=args.backend,
        db_url=args.db_url,
    )
    if crawl_result["returncode"] != 0:
        print(
            json.dumps(
                {
                    "test_result": test_result,
                    "crawl_result": crawl_result,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(1)

    samples = read_samples(
        db_path=args.db_path,
        sample_limit=args.sample_limit,
        backend=args.backend,
        db_url=args.db_url,
    )
    payload = {
        "test_result": {
            "command": test_result["command"],
            "returncode": test_result["returncode"],
        },
        "crawl_result": {
            "command": crawl_result["command"],
            "returncode": crawl_result["returncode"],
            "summary": crawl_result["parsed_output"],
        },
        "db_result": samples,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
