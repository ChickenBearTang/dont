from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

from consumption_poc.config import RAW_DATA_DIR, GENERATED_DATA_DIR

def clear_directory(target_dir: Path) -> None:
    if not target_dir.exists():
        return
    for path in target_dir.rglob("*"):
        if path.is_file():
            path.unlink()

def generate_users() -> list[dict]:
    users = []
    for i in range(1, 11):
        users.append({
            "user_id": f"U{2000+i}",
            "name": f"싸피생{i}",
            "age": random.randint(24, 29),
            "job": "SSAFY 교육생",
            "monthly_income": random.choice([1000000, 1300000]),
            "pay_day": 10,
            "residence_type": "자취",
            "main_bank": "국민은행",
            "main_card_type": "체크카드"
        })
    return users

def get_ssafy_merchants(category: str) -> list[str]:
    if category == "식비":
        return ["역삼동 샐러디", "강남역 국밥집", "맥도날드 역삼점", "싸피 구내식당", "역삼 마라탕", "배달의민족", "요기요"]
    elif category == "카페/간식":
        return ["스타벅스 역삼역점", "메가커피 강남점", "더벤티 르네상스사거리점", "씨유 역삼점", "GS25 강남역점"]
    elif category == "교통":
        return ["지하철(신분당선)", "지하철(2호선)", "카카오T", "광역버스"]
    elif category == "쇼핑/온라인":
        return ["쿠팡", "네이버페이", "무신사", "올리브영 역삼점", "강남역 다이소"]
    elif category == "구독/정기결제":
        return ["넷플릭스", "유튜브프리미엄", "챗GPT", "Github Copilot"]
    return ["기타 매장"]

def get_random_datetime(base_month: datetime, is_weekend: bool = False, late_night: bool = False) -> datetime:
    day = random.randint(1, 28)
    dt = base_month.replace(day=day)

    while (dt.weekday() >= 5) != is_weekend:
        day = random.randint(1, 28)
        dt = base_month.replace(day=day)

    hour = random.randint(23, 24) % 24 if late_night else random.randint(8, 22)
    minute = random.randint(0, 59)
    return dt.replace(hour=hour, minute=minute)

def generate_transactions(users: list[dict], months: list[datetime]) -> tuple[list[dict], list[dict]]:
    transactions = []
    account_transactions = []
    card_tx_id_counter = 10000
    acc_tx_id_counter = 50000

    categories = ["식비", "카페/간식", "교통", "쇼핑/온라인", "구독/정기결제"]
    weights = [40, 20, 15, 20, 5]

    for user in users:
        balance = 5000000  # Default starting balance

        for month in months:
            dt_payday = month.replace(day=10, hour=10, minute=0)
            balance += user["monthly_income"]
            account_transactions.append({
                "transaction_id": f"A{acc_tx_id_counter}",
                "user_id": user["user_id"],
                "transacted_at": dt_payday.isoformat(),
                "type": "in",
                "counterparty": "SSAFY지원금" if user["monthly_income"] == 1000000 else "SSAFY지원금+a",
                "amount": user["monthly_income"],
                "category": "수입",
                "subcategory": "급여",
                "balance_after": balance
            })
            acc_tx_id_counter += 1

            target_spend = int(user["monthly_income"] * random.uniform(0.8, 1.1))
            current_spend = 0

            for sub in ["넷플릭스", "유튜브프리미엄"]:
                amount = 17000 if sub == "넷플릭스" else 14900
                dt = month.replace(day=1, hour=10, minute=0)
                transactions.append({
                    "transaction_id": f"T{card_tx_id_counter}",
                    "user_id": user["user_id"],
                    "approved_at": dt.isoformat(),
                    "merchant_name": sub,
                    "amount": amount,
                    "category": "구독/정기결제",
                    "subcategory": "엔터테인먼트",
                    "payment_method": user["main_card_type"],
                    "status": "approved",
                    "is_recurring": "true"
                })
                card_tx_id_counter += 1
                current_spend += amount

            while current_spend < target_spend:
                cat = random.choices(categories, weights=weights)[0]
                merchant = random.choice(get_ssafy_merchants(cat))

                is_weekend = random.random() < 0.2
                late_night = random.random() < 0.05
                dt = get_random_datetime(month, is_weekend, late_night)

                amount = random.randint(4000, 30000)
                if cat == "쇼핑/온라인":
                    amount = random.randint(15000, 100000)
                elif merchant == "싸피 구내식당":
                    amount = 5500

                if cat == "쇼핑/온라인" and late_night:
                    amount = random.randint(50000, 300000)

                if current_spend + amount > target_spend * 1.1:
                    break

                transactions.append({
                    "transaction_id": f"T{card_tx_id_counter}",
                    "user_id": user["user_id"],
                    "approved_at": dt.isoformat(),
                    "merchant_name": merchant,
                    "amount": amount,
                    "category": cat,
                    "subcategory": "일반",
                    "payment_method": user["main_card_type"],
                    "status": "approved",
                    "is_recurring": "false"
                })
                card_tx_id_counter += 1
                current_spend += amount

            dt_bill = month.replace(day=25, hour=18, minute=0)
            balance -= current_spend
            account_transactions.append({
                "transaction_id": f"A{acc_tx_id_counter}",
                "user_id": user["user_id"],
                "transacted_at": dt_bill.isoformat(),
                "type": "out",
                "counterparty": "카드대금결제",
                "amount": current_spend,
                "category": "card_bill",
                "subcategory": "card",
                "balance_after": balance
            })
            acc_tx_id_counter += 1

    return transactions, account_transactions

def main():
    print("Clearing old data...")
    clear_directory(RAW_DATA_DIR)
    clear_directory(GENERATED_DATA_DIR)

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating SSAFY users...")
    users = generate_users()
    with open(RAW_DATA_DIR / "user_profile.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

    print("Generating SSAFY transactions...")
    start_date = datetime(2025, 10, 1)
    months = [
        datetime(2025, 10, 1),
        datetime(2025, 11, 1),
        datetime(2025, 12, 1),
        datetime(2026, 1, 1),
        datetime(2026, 2, 1),
        datetime(2026, 3, 1)
    ]

    card_transactions, account_transactions = generate_transactions(users, months)

    with open(RAW_DATA_DIR / "card_transactions.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "transaction_id", "user_id", "approved_at", "merchant_name",
            "amount", "category", "subcategory", "payment_method", "status", "is_recurring"
        ])
        writer.writeheader()
        writer.writerows(card_transactions)

    with open(RAW_DATA_DIR / "account_transactions.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "transaction_id", "user_id", "transacted_at", "type",
            "counterparty", "amount", "category", "subcategory", "balance_after"
        ])
        writer.writeheader()
        writer.writerows(account_transactions)

    print("New SSAFY mock data generated successfully in data/raw.")
    print("You should now run `scripts/regenerate_reports.py` to recreate AI reports.")

if __name__ == "__main__":
    main()
