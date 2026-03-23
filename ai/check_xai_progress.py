from __future__ import annotations

import json
import subprocess
import sys


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ai", *args],
        text=True,
        capture_output=True,
        timeout=40,
        check=False,
    )


def main() -> int:
    first = _run("--xai", "--top-k", "2")
    if first.returncode != 0:
        print(first.stderr)
        return 1
    payload = json.loads(first.stdout.strip())
    required = {"schema_version", "explanations", "analysis"}
    if not required.issubset(payload.keys()):
        print({"missing": sorted(required - set(payload.keys()))})
        return 1

    suite_1 = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "ai/tests",
            "-p",
            "test_*xai*.py",
        ],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if suite_1.returncode != 0:
        print(suite_1.stdout)
        print(suite_1.stderr)
        return 1

    suite_2 = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "ai.tests.test_crawler_hot_deal",
            "ai.tests.test_main_xai",
        ],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if suite_2.returncode != 0:
        print(suite_2.stdout)
        print(suite_2.stderr)
        return 1

    print("XAI progress checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
