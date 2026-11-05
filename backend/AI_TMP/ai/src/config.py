from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
# 서비스가 실행 중에 쓰는 파일(사용자 반응, 감사 로그, 입력 스냅샷)의 위치. 기본은 DATA_DIR 이지만 DATA_DIR 에는
# 이미지에 들어 있는 모델 파일(artifacts)도 있어서, 컨테이너에서는 AI_RUNTIME_DIR 로 따로 잡아 볼륨을 붙인다
# (DATA_DIR 전체에 볼륨을 붙이면 이미지가 새 모델을 담아도 볼륨의 옛 파일이 가려 버린다).
RUNTIME_DIR = Path(os.environ.get("AI_RUNTIME_DIR") or DATA_DIR)
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
ENV_PATH = BASE_DIR / "../../../.env"


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
