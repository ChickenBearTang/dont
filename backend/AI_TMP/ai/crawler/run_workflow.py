from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys


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
) -> dict[str, object]:
    command = [
        sys.executable,
        "-m",
        "ai.crawler.run_to_sqlite",
        "--db-path",
        db_path,
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


def read_samples(db_path: str, sample_limit: int) -> dict[str, object]:
    with sqlite3.connect(db_path) as connection:
        total_count = connection.execute("SELECT COUNT(*) FROM crawl_items").fetchone()[
            0
        ]
        rows = connection.execute(
            """
            SELECT post_id, title, price, url
            FROM crawl_items
            ORDER BY CAST(post_id AS INTEGER) DESC
            LIMIT ?
            """,
            (sample_limit,),
        ).fetchall()

    samples = [
        {
            "post_id": row[0],
            "title": row[1],
            "price": row[2],
            "url": row[3],
        }
        for row in rows
    ]
    return {
        "total_count": total_count,
        "sample_items": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default="ai/data/crawl.db")
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=2)
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

    samples = read_samples(db_path=args.db_path, sample_limit=args.sample_limit)
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
