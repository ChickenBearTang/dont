from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "ai" / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
GENERATED_DATA_DIR = DATA_DIR / "generated"
FRONTEND_DIR = BASE_DIR / "frontend"

USER_PROFILE_PATH = RAW_DATA_DIR / "user_profile.json"
CARD_TRANSACTIONS_PATH = RAW_DATA_DIR / "card_transactions.csv"
ACCOUNT_TRANSACTIONS_PATH = RAW_DATA_DIR / "account_transactions.csv"

GENERATED_MONTHLY_PATH = GENERATED_DATA_DIR / "consumption_report_monthly.csv"
GENERATED_CATEGORY_PATH = GENERATED_DATA_DIR / "consumption_report_category.csv"
GENERATED_TIME_PATH = GENERATED_DATA_DIR / "consumption_report_time.csv"
GENERATED_ANOMALY_PATH = GENERATED_DATA_DIR / "consumption_report_anomalies.csv"
GENERATED_CASHFLOW_PATH = GENERATED_DATA_DIR / "cashflow_report_monthly.csv"
GENERATED_SUMMARY_PATH = GENERATED_DATA_DIR / "consumption_report_summary.json"

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_MODEL_FALLBACKS = (
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
)
ENV_PATH = BASE_DIR / ".env"


def load_local_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_PATH.exists():
        return values

    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name) or load_local_env().get(name, default)
