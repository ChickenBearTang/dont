"""XAI 랩 페이지를 로컬에서 띄운다.

    cd backend/AI_TMP
    python -m ai.scripts.run_xai_lab            # http://127.0.0.1:8765/xai-lab
    python -m ai.scripts.run_xai_lab --port 9000

DB, Spring, 외부 네트워크 없이 돈다. 랩은 모델 내부를 보여주므로 이 스크립트가
AI_XAI_LAB_ENABLED=1 을 켠 프로세스에서만 열린다 (운영 서버는 기본으로 404).
127.0.0.1 에만 바인딩한다. 다른 기기에서 보려면 --host 0.0.0.0 을 직접 지정한다.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the XAI lab page")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    os.environ["AI_XAI_LAB_ENABLED"] = "1"
    sys.path.insert(0, str(SRC_DIR))
    import uvicorn

    print(f"XAI 랩: http://{args.host}:{args.port}/xai-lab")
    uvicorn.run("main:app", host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
