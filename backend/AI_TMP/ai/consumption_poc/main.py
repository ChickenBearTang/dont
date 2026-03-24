from __future__ import annotations

import sys
from pathlib import Path


# Compatibility shim:
# keep older startup commands like `uvicorn consumption_poc.main:app`
# working while routing to the actual DB-backed FastAPI app in `ai/src`.
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from main import app  # noqa: E402

