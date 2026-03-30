from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from domain.consumption.schemas import AccountTransaction, CardTransaction, UserProfile


CARD_REQUIRED_FIELDS = {
    "transaction_id",
    "user_id",
    "approved_at",
    "merchant_name",
    "amount",
    "category",
    "subcategory",
    "payment_method",
    "status",
    "is_recurring",
}

ACCOUNT_REQUIRED_FIELDS = {
    "transaction_id",
    "user_id",
    "transacted_at",
    "type",
    "counterparty",
    "amount",
    "category",
    "subcategory",
    "balance_after",
}


def _validate_fields(path: Path, required_fields: set[str], actual_fields: set[str]) -> None:
    missing = required_fields - actual_fields
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"{path.name}에 필수 필드가 누락되었습니다: {missing_text}")


def load_user_profile(path: Path) -> UserProfile:
    return load_user_profiles(path)[0]


def load_user_profiles(path: Path) -> list[UserProfile]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)

    profiles: list[UserProfile] = []
    if isinstance(payload, dict):
        payload_items = [payload]
    elif isinstance(payload, list):
        payload_items = payload
    else:
        raise ValueError(f"{path.name}의 사용자 프로필 형식이 올바르지 않습니다.")

    for item in payload_items:
        profiles.append(UserProfile(**item))

    if not profiles:
        raise ValueError(f"사용자 프로필 파일이 비어 있습니다: {path.name}")

    return profiles


def load_card_transactions(path: Path) -> list[CardTransaction]:
    with path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        _validate_fields(path, CARD_REQUIRED_FIELDS, set(reader.fieldnames or []))
        rows = []
        for row in reader:
            rows.append(
                CardTransaction(
                    transaction_id=row["transaction_id"],
                    user_id=row["user_id"],
                    approved_at=datetime.fromisoformat(row["approved_at"]),
                    merchant_name=row["merchant_name"],
                    amount=int(row["amount"]),
                    category=row["category"],
                    subcategory=row["subcategory"],
                    payment_method=row["payment_method"],
                    status=row["status"],
                    is_recurring=row["is_recurring"].strip().lower() == "true",
                )
            )
    return rows


def load_account_transactions(path: Path) -> list[AccountTransaction]:
    with path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        _validate_fields(path, ACCOUNT_REQUIRED_FIELDS, set(reader.fieldnames or []))
        rows = []
        for row in reader:
            rows.append(
                AccountTransaction(
                    transaction_id=row["transaction_id"],
                    user_id=row["user_id"],
                    transacted_at=datetime.fromisoformat(row["transacted_at"]),
                    transaction_type=row["type"],
                    counterparty=row["counterparty"],
                    amount=int(row["amount"]),
                    category=row["category"],
                    subcategory=row["subcategory"],
                    balance_after=int(row["balance_after"]),
                )
            )
    return rows
