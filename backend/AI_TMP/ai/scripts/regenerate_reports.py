from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from consumption_poc.service import ReportService


def main() -> None:
    service = ReportService()
    generated_files = service.regenerate()
    print("Generated:")
    for generated_file in generated_files:
        print(f"- {generated_file}")


if __name__ == "__main__":
    main()
