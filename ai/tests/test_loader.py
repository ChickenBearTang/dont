from __future__ import annotations

import csv

import pytest

from consumption_poc.config import CARD_TRANSACTIONS_PATH
from consumption_poc.loader import load_card_transactions


def test_utf8_card_loader_reads_korean_text() -> None:
    transactions = load_card_transactions(CARD_TRANSACTIONS_PATH)
    assert transactions[0].merchant_name == "스타벅스 강남점"


def test_loader_raises_when_required_field_is_missing(tmp_path) -> None:
    path = tmp_path / "broken.csv"
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(["transaction_id", "user_id"])
        writer.writerow(["C1", "U1"])

    with pytest.raises(ValueError, match="Missing required fields"):
        load_card_transactions(path)
