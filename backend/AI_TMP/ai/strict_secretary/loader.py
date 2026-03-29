from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from consumption_poc.loader import load_user_profiles, load_card_transactions
from consumption_poc.models import UserProfile, CardTransaction

def get_user_profile(data_dir: Path, user_id: str) -> UserProfile:
    profiles = load_user_profiles(data_dir / "raw" / "user_profile.json")
    for profile in profiles:
        if profile.user_id == user_id:
            return profile
    raise ValueError(f"User profile for {user_id} not found.")

def get_recent_card_transactions(data_dir: Path, user_id: str, months_back: int = 3) -> list[CardTransaction]:
    """Retrieve recent card transactions for a specific user to prevent sending too much data to LLM."""
    all_txs = load_card_transactions(data_dir / "raw" / "card_transactions.csv")
    user_txs = [tx for tx in all_txs if tx.user_id == user_id]

    if not user_txs:
        return []

    latest_date = max(tx.approved_at for tx in user_txs)

    recent_txs = []
    for tx in user_txs:
        days_diff = (latest_date - tx.approved_at).days
        if days_diff <= months_back * 30:
            recent_txs.append(tx)

    return recent_txs

def get_explain_logs(data_dir: Path, user_id: str) -> list[dict]:
    """Mock loading explain logs from previous conversations."""
    return [
        {"date": "2026-03-01", "item": "고급 오마카세", "excuse": "오랜만에 만난 친구한테 내가 쏘기로 했음. 이건 진짜 어쩔 수 없는 지출임!"},
        {"date": "2026-02-15", "item": "닌텐도 스위치 게임", "excuse": "스트레스 받아서 충동구매함... 앞으로 안 그럴게요ㅠ"}
    ]

def get_latest_ai_report(data_dir: Path, user_id: str) -> dict | None:
    """Retrieve the latest monthly AI spending report for context."""
    user_gen_dir = data_dir / "generated" / "users" / user_id
    if not user_gen_dir.exists():
        return None

    month_dirs = [d for d in user_gen_dir.iterdir() if d.is_dir() and d.name.startswith("20")]
    if not month_dirs:
        return None

    latest_month = max(month_dirs, key=lambda d: d.name)
    report_file = latest_month / "period_summary.json"

    if report_file.exists():
        with report_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    return None
