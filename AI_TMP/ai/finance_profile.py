from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "current_balance": ("current_balance", "currentBalance"),
    "emergency_fund_balance": ("emergency_fund_balance", "emergencyFundBalance"),
    "expected_card_payment_amount": (
        "expected_card_payment_amount",
        "expectedCardPaymentAmount",
    ),
    "days_until_card_due": ("days_until_card_due", "daysUntilCardDue"),
}


def _pick(payload: dict[str, Any], candidates: tuple[str, ...]) -> Any:
    for key in candidates:
        if key in payload:
            return payload[key]
    return None


def fetch_finance_profile(
    url: str, *, timeout: int = 3
) -> dict[str, float | int] | None:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "wt-ai-finance-client/1.0",
        },
    )
    try:
        with urlopen(request, timeout=max(timeout, 1)) as response:
            body = response.read().decode("utf-8")
    except OSError:
        return None

    try:
        raw = json.loads(body)
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict):
        return None

    current_balance_raw = _pick(raw, _FIELD_ALIASES["current_balance"])
    emergency_fund_raw = _pick(raw, _FIELD_ALIASES["emergency_fund_balance"])
    expected_card_raw = _pick(raw, _FIELD_ALIASES["expected_card_payment_amount"])
    due_days_raw = _pick(raw, _FIELD_ALIASES["days_until_card_due"])

    if (
        current_balance_raw is None
        or emergency_fund_raw is None
        or expected_card_raw is None
        or due_days_raw is None
    ):
        return None

    try:
        profile = {
            "current_balance": float(current_balance_raw),
            "emergency_fund_balance": float(emergency_fund_raw),
            "expected_card_payment_amount": float(expected_card_raw),
            "days_until_card_due": int(due_days_raw),
        }
    except (TypeError, ValueError):
        return None

    return profile
