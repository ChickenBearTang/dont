from __future__ import annotations

import calendar
import csv
import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
USER_PROFILE_PATH = RAW_DIR / "user_profile.json"
CARD_TRANSACTIONS_PATH = RAW_DIR / "card_transactions.csv"
ACCOUNT_TRANSACTIONS_PATH = RAW_DIR / "account_transactions.csv"


MONTHS = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"]


@dataclass(frozen=True)
class UserSeed:
    user_id: str
    name: str
    age: int
    job: str
    monthly_income: int
    pay_day: int
    residence_type: str
    main_bank: str
    main_card_type: str
    opening_balance: int
    rent: int
    telecom: int
    utility: int
    insurance: int
    monthly_card_count: tuple[int, int]
    merchants: list[tuple[str, str, str, tuple[int, int], list[int], int]]
    side_income_months: dict[str, tuple[str, int]]
    anomaly_rules: dict[str, tuple[str, str, str, int, int, int]]


USERS: list[UserSeed] = [
    UserSeed(
        user_id="U1001",
        name="Kim Minsoo",
        age=29,
        job="office_worker",
        monthly_income=3200000,
        pay_day=25,
        residence_type="rent",
        main_bank="Hanbit Bank",
        main_card_type="credit_card",
        opening_balance=1320000,
        rent=850000,
        telecom=65000,
        utility=42000,
        insurance=0,
        monthly_card_count=(42, 54),
        merchants=[
            ("Cafe A", "food", "cafe", (3900, 7200), [7, 8, 9], 18),
            ("Coupang", "shopping", "ecommerce", (18000, 89000), [12, 13, 21], 8),
            ("Baedal", "food", "delivery", (17000, 34000), [19, 20, 21, 22], 12),
            ("GS25 Gangnam", "food", "convenience_store", (2800, 12800), [8, 23], 10),
            ("OliveYoung", "shopping", "health_beauty", (12000, 36000), [18, 19], 5),
            ("MegaCafe", "food", "cafe", (2500, 4700), [8], 10),
            ("Netflix", "subscription", "ott", (17000, 17000), [20], 2),
            ("Kyobo Bookstore", "shopping", "book", (13000, 27000), [13, 14], 3),
            ("Subway", "food", "fastfood", (7900, 10900), [12, 13], 4),
        ],
        side_income_months={"2025-12": ("year_end_bonus", 500000)},
        anomaly_rules={
            "2025-12": ("Premium Hotel", "travel", "hotel", 420000, 22, 22),
        },
    ),
    UserSeed(
        user_id="U1002",
        name="Lee Ji",
        age=33,
        job="freelancer",
        monthly_income=2800000,
        pay_day=24,
        residence_type="rent",
        main_bank="BlueBank",
        main_card_type="credit_card",
        opening_balance=980000,
        rent=700000,
        telecom=50000,
        utility=32000,
        insurance=48000,
        monthly_card_count=(38, 50),
        merchants=[
            ("Market One", "food", "groceries", (9000, 28000), [11, 18], 14),
            ("Cafe Nova", "food", "cafe", (4800, 9800), [8, 9, 15], 14),
            ("DeliveryX", "food", "delivery", (16000, 28000), [19, 20], 9),
            ("Streaming Co", "subscription", "ott", (17000, 17000), [20], 2),
            ("Home Depot", "shopping", "home", (12000, 52000), [13, 17], 6),
            ("Style Shop", "shopping", "fashion", (18000, 86000), [20], 5),
            ("Taxi Go", "transport", "taxi", (9000, 23000), [22, 23], 4),
            ("Office Meal", "food", "fastfood", (7800, 14000), [12, 13], 6),
        ],
        side_income_months={"2026-02": ("project_income", 650000)},
        anomaly_rules={"2026-03": ("Designer Chair", "shopping", "home", 310000, 20, 23)},
    ),
    UserSeed(
        user_id="U1003",
        name="Park Hana",
        age=26,
        job="student",
        monthly_income=2200000,
        pay_day=20,
        residence_type="dormitory",
        main_bank="GreenBank",
        main_card_type="credit_card",
        opening_balance=740000,
        rent=600000,
        telecom=45000,
        utility=29000,
        insurance=0,
        monthly_card_count=(34, 44),
        merchants=[
            ("Breakfast House", "food", "fastfood", (5500, 9800), [8, 9], 10),
            ("Book Mart", "shopping", "book", (9000, 24000), [13, 18], 8),
            ("Green Market", "food", "groceries", (12000, 26000), [12, 18], 12),
            ("DeliveryY", "food", "delivery", (13000, 22000), [19, 20], 6),
            ("Sport Mart", "shopping", "sports", (14000, 42000), [16, 18], 3),
            ("Campus Cafe", "food", "cafe", (2800, 6200), [10, 15], 9),
            ("Bus Fare", "transport", "public_transit", (1400, 1800), [8, 18], 14),
            ("Design Store", "shopping", "fashion", (12000, 36000), [18, 19], 4),
        ],
        side_income_months={"2026-01": ("scholarship", 400000)},
        anomaly_rules={"2025-11": ("Tablet Store", "shopping", "electronics", 280000, 18, 21)},
    ),
    UserSeed(
        user_id="U1004",
        name="Choi Sun",
        age=41,
        job="manager",
        monthly_income=5100000,
        pay_day=25,
        residence_type="own",
        main_bank="Union Bank",
        main_card_type="credit_card",
        opening_balance=2800000,
        rent=0,
        telecom=89000,
        utility=71000,
        insurance=220000,
        monthly_card_count=(46, 62),
        merchants=[
            ("Family Mart", "food", "groceries", (18000, 48000), [18, 19], 14),
            ("Fuel Max", "transport", "fuel", (55000, 98000), [7, 8], 6),
            ("Steak House", "food", "dining", (42000, 128000), [19, 20], 8),
            ("Department Store", "shopping", "fashion", (25000, 145000), [15, 20], 7),
            ("Cinema Box", "leisure", "movie", (13000, 38000), [20, 21], 4),
            ("Gym Pro", "health", "fitness", (69000, 69000), [7], 2),
            ("Kid Academy", "education", "academy", (180000, 180000), [10], 1),
            ("Cafe Lane", "food", "cafe", (4200, 9800), [8, 15], 10),
        ],
        side_income_months={"2025-12": ("performance_bonus", 1200000)},
        anomaly_rules={"2026-02": ("Airline Ticket", "travel", "flight", 530000, 13, 15)},
    ),
    UserSeed(
        user_id="U1005",
        name="Jung Ara",
        age=31,
        job="designer",
        monthly_income=3500000,
        pay_day=25,
        residence_type="rent",
        main_bank="Orange Bank",
        main_card_type="credit_card",
        opening_balance=1210000,
        rent=930000,
        telecom=62000,
        utility=44000,
        insurance=71000,
        monthly_card_count=(44, 58),
        merchants=[
            ("Brunch Atelier", "food", "dining", (18000, 36000), [11, 13], 10),
            ("Style Shop", "shopping", "fashion", (22000, 118000), [16, 20], 10),
            ("Canvas Market", "shopping", "living", (12000, 52000), [14, 18], 7),
            ("Cafe Nova", "food", "cafe", (4800, 9200), [9, 10, 15], 12),
            ("DeliveryX", "food", "delivery", (14000, 28000), [19, 22], 8),
            ("Photo Lab", "leisure", "hobby", (12000, 56000), [17, 19], 4),
            ("Music Plus", "subscription", "music", (10900, 10900), [10], 2),
            ("Cabin Hotel", "travel", "hotel", (95000, 220000), [20, 22], 2),
        ],
        side_income_months={"2026-03": ("freelance_income", 370000)},
        anomaly_rules={"2026-01": ("Luxury Bag House", "shopping", "luxury", 460000, 21, 23)},
    ),
    UserSeed(
        user_id="U1006",
        name="Yoon Tae",
        age=38,
        job="engineer",
        monthly_income=4300000,
        pay_day=25,
        residence_type="rent",
        main_bank="Metro Bank",
        main_card_type="credit_card",
        opening_balance=1630000,
        rent=1100000,
        telecom=59000,
        utility=51000,
        insurance=96000,
        monthly_card_count=(40, 52),
        merchants=[
            ("Coupang", "shopping", "ecommerce", (18000, 82000), [12, 21], 8),
            ("Office Cafe", "food", "cafe", (3200, 7100), [8, 9], 14),
            ("Subway", "food", "fastfood", (7900, 11200), [12, 13], 8),
            ("Fuel Max", "transport", "fuel", (48000, 84000), [7, 8], 5),
            ("Game Box", "leisure", "gaming", (18000, 65000), [20, 23], 4),
            ("Streaming Co", "subscription", "ott", (17000, 17000), [20], 2),
            ("Electro Mart", "shopping", "electronics", (22000, 180000), [19, 21], 4),
            ("DeliveryX", "food", "delivery", (16000, 29000), [20, 22], 7),
        ],
        side_income_months={"2025-12": ("stock_dividend", 240000)},
        anomaly_rules={"2026-03": ("Gaming Laptop", "shopping", "electronics", 690000, 23, 23)},
    ),
    UserSeed(
        user_id="U1007",
        name="Seo Bomi",
        age=35,
        job="teacher",
        monthly_income=3000000,
        pay_day=25,
        residence_type="rent",
        main_bank="Clover Bank",
        main_card_type="credit_card",
        opening_balance=870000,
        rent=780000,
        telecom=54000,
        utility=36000,
        insurance=58000,
        monthly_card_count=(36, 48),
        merchants=[
            ("School Lunch", "food", "fastfood", (6500, 9800), [12, 13], 10),
            ("Local Market", "food", "groceries", (12000, 26000), [18, 19], 12),
            ("Book Mart", "shopping", "book", (9000, 26000), [17, 19], 8),
            ("Cafe Lane", "food", "cafe", (3800, 7200), [8, 16], 8),
            ("DeliveryY", "food", "delivery", (13000, 25000), [19, 21], 6),
            ("Online Class", "education", "course", (15000, 72000), [20], 4),
            ("Streaming Co", "subscription", "ott", (17000, 17000), [20], 2),
            ("Clinic Care", "health", "medical", (18000, 62000), [11, 18], 4),
        ],
        side_income_months={"2026-02": ("private_tutoring", 280000)},
        anomaly_rules={"2025-12": ("Travel Agency", "travel", "package", 340000, 19, 21)},
    ),
    UserSeed(
        user_id="U1008",
        name="Han Doyun",
        age=27,
        job="startup_operator",
        monthly_income=3900000,
        pay_day=25,
        residence_type="rent",
        main_bank="River Bank",
        main_card_type="credit_card",
        opening_balance=1450000,
        rent=990000,
        telecom=61000,
        utility=47000,
        insurance=0,
        monthly_card_count=(48, 66),
        merchants=[
            ("Taxi Go", "transport", "taxi", (9000, 26000), [22, 23], 10),
            ("Night Delivery", "food", "delivery", (18000, 36000), [21, 23], 12),
            ("Office Cafe", "food", "cafe", (3200, 6900), [8, 9, 10], 14),
            ("Coupang", "shopping", "ecommerce", (18000, 88000), [12, 20], 8),
            ("Premium Gym", "health", "fitness", (79000, 79000), [7], 2),
            ("Streaming Co", "subscription", "ott", (17000, 17000), [20], 2),
            ("Bar 45", "leisure", "bar", (19000, 78000), [21, 23], 6),
            ("Convenience Hub", "food", "convenience_store", (2400, 11800), [0, 8, 23], 10),
        ],
        side_income_months={"2026-01": ("side_project", 420000)},
        anomaly_rules={"2026-02": ("International Flight", "travel", "flight", 610000, 1, 3)},
    ),
]


FIXED_U1001_Q1 = [
    ("C202601001", "U1001", "2026-01-02T08:12:00", "Cafe A", 6100, "food", "cafe", "credit_card", "approved", False),
    ("C202601002", "U1001", "2026-01-03T12:24:00", "Coupang", 42800, "shopping", "ecommerce", "credit_card", "approved", False),
    ("C202601003", "U1001", "2026-01-04T19:08:00", "Baedal", 23900, "food", "delivery", "credit_card", "approved", False),
    ("C202601004", "U1001", "2026-01-05T08:41:00", "GS25 Gangnam", 4800, "food", "convenience_store", "credit_card", "approved", False),
    ("C202601005", "U1001", "2026-01-07T18:32:00", "OliveYoung", 22100, "shopping", "health_beauty", "credit_card", "approved", False),
    ("C202601006", "U1001", "2026-01-09T07:58:00", "MegaCafe", 3000, "food", "cafe", "credit_card", "approved", False),
    ("C202601007", "U1001", "2026-01-10T20:13:00", "Netflix", 17000, "subscription", "ott", "credit_card", "approved", True),
    ("C202601008", "U1001", "2026-01-12T13:11:00", "McDonalds", 8900, "food", "fastfood", "credit_card", "approved", False),
    ("C202601009", "U1001", "2026-01-15T22:43:00", "Yogiyo", 31200, "food", "delivery", "credit_card", "approved", False),
    ("C202601010", "U1001", "2026-01-18T10:02:00", "Kyobo Bookstore", 18700, "shopping", "book", "credit_card", "approved", False),
    ("C202601011", "U1001", "2026-01-21T08:17:00", "Kommerce Cafe", 4100, "food", "cafe", "credit_card", "approved", False),
    ("C202601012", "U1001", "2026-01-24T23:51:00", "GS25 Gangnam", 12900, "food", "convenience_store", "credit_card", "approved", False),
    ("C202602001", "U1001", "2026-02-01T11:20:00", "Musinsa", 75900, "shopping", "fashion", "credit_card", "approved", False),
    ("C202602002", "U1001", "2026-02-03T08:09:00", "Cafe A", 5900, "food", "cafe", "credit_card", "approved", False),
    ("C202602003", "U1001", "2026-02-05T19:26:00", "Baedal", 19800, "food", "delivery", "credit_card", "approved", False),
    ("C202602004", "U1001", "2026-02-07T14:42:00", "GS25 Gangnam", 6700, "food", "convenience_store", "credit_card", "approved", False),
    ("C202602005", "U1001", "2026-02-10T20:14:00", "Netflix", 17000, "subscription", "ott", "credit_card", "approved", True),
    ("C202602006", "U1001", "2026-02-11T12:36:00", "Subway", 9900, "food", "fastfood", "credit_card", "approved", False),
    ("C202602007", "U1001", "2026-02-14T18:55:00", "Casa Home", 64800, "shopping", "home", "credit_card", "approved", False),
    ("C202602008", "U1001", "2026-02-16T08:01:00", "MegaCafe", 3200, "food", "cafe", "credit_card", "approved", False),
    ("C202602009", "U1001", "2026-02-18T21:47:00", "Yogiyo", 28400, "food", "delivery", "credit_card", "approved", False),
    ("C202602010", "U1001", "2026-02-20T13:05:00", "Daiso", 8300, "shopping", "living", "credit_card", "approved", False),
    ("C202602011", "U1001", "2026-02-22T09:12:00", "GS25 Gangnam", 5400, "food", "convenience_store", "credit_card", "approved", False),
    ("C202602012", "U1001", "2026-02-26T01:18:00", "Luxury Watch Store", 890000, "shopping", "luxury", "credit_card", "approved", False),
    ("C202603001", "U1001", "2026-03-01T12:18:00", "Coupang", 39100, "shopping", "ecommerce", "credit_card", "approved", False),
    ("C202603002", "U1001", "2026-03-02T08:16:00", "Cafe A", 6300, "food", "cafe", "credit_card", "approved", False),
    ("C202603003", "U1001", "2026-03-04T19:02:00", "Baedal", 25400, "food", "delivery", "credit_card", "approved", False),
    ("C202603004", "U1001", "2026-03-05T08:34:00", "CU", 5100, "food", "convenience_store", "credit_card", "approved", False),
    ("C202603005", "U1001", "2026-03-08T20:15:00", "Netflix", 17000, "subscription", "ott", "credit_card", "approved", True),
    ("C202603006", "U1001", "2026-03-09T12:09:00", "MamSt", 9400, "food", "fastfood", "credit_card", "approved", False),
    ("C202603007", "U1001", "2026-03-12T18:21:00", "OliveYoung", 27400, "shopping", "health_beauty", "credit_card", "approved", False),
    ("C202603008", "U1001", "2026-03-14T08:05:00", "MegaCafe", 3200, "food", "cafe", "credit_card", "approved", False),
    ("C202603009", "U1001", "2026-03-17T21:26:00", "Yogiyo", 33600, "food", "delivery", "credit_card", "approved", False),
    ("C202603010", "U1001", "2026-03-19T13:17:00", "Kyobo Bookstore", 15400, "shopping", "book", "credit_card", "approved", False),
    ("C202603011", "U1001", "2026-03-22T07:49:00", "GS25 Gangnam", 4600, "food", "convenience_store", "credit_card", "approved", False),
    ("C202603012", "U1001", "2026-03-27T23:58:00", "CU", 11800, "food", "convenience_store", "credit_card", "approved", False),
]


def month_last_day(month: str) -> int:
    year, month_num = month.split("-")
    return calendar.monthrange(int(year), int(month_num))[1]


def card_id(user_id: str, month: str, sequence: int) -> str:
    suffix = user_id[-2:]
    return f"C{suffix}{month.replace('-', '')}{sequence:03d}"


def account_id(user_id: str, month: str, sequence: int) -> str:
    suffix = user_id[-2:]
    return f"A{suffix}{month.replace('-', '')}{sequence:03d}"


def make_rng(user_id: str, month: str) -> random.Random:
    seed = int("".join(filter(str.isdigit, user_id + month.replace("-", ""))))
    return random.Random(seed)


def generate_card_transactions(user: UserSeed) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    fixed_months = {"2026-01", "2026-02", "2026-03"} if user.user_id == "U1001" else set()

    for fixed in FIXED_U1001_Q1 if user.user_id == "U1001" else []:
        (
            transaction_id,
            user_id,
            approved_at,
            merchant_name,
            amount,
            category,
            subcategory,
            payment_method,
            status,
            is_recurring,
        ) = fixed
        rows.append(
            {
                "transaction_id": transaction_id,
                "user_id": user_id,
                "approved_at": approved_at,
                "merchant_name": merchant_name,
                "amount": amount,
                "category": category,
                "subcategory": subcategory,
                "payment_method": payment_method,
                "status": status,
                "is_recurring": str(is_recurring).lower(),
            }
        )

    for month in MONTHS:
        if month in fixed_months:
            continue
        rng = make_rng(user.user_id, month)
        count = rng.randint(*user.monthly_card_count)
        recurring_tracker: set[tuple[str, str]] = set()
        for index in range(1, count + 1):
            merchant, category, subcategory, amount_range, hours, weight = rng.choice(
                [merchant for merchant in user.merchants for _ in range(merchant[5])]
            )
            day = rng.randint(1, month_last_day(month))
            hour = rng.choice(hours)
            minute = rng.randint(0, 59)
            amount = rng.randint(amount_range[0], amount_range[1])
            is_recurring = category == "subscription"
            if is_recurring and (merchant, month) in recurring_tracker:
                continue
            recurring_tracker.add((merchant, month))
            rows.append(
                {
                    "transaction_id": card_id(user.user_id, month, index),
                    "user_id": user.user_id,
                    "approved_at": f"{month}-{day:02d}T{hour:02d}:{minute:02d}:00",
                    "merchant_name": merchant,
                    "amount": amount,
                    "category": category,
                    "subcategory": subcategory,
                    "payment_method": "credit_card",
                    "status": "approved",
                    "is_recurring": str(is_recurring).lower(),
                }
            )

        if month in user.anomaly_rules:
            merchant, category, subcategory, amount, hour, day = user.anomaly_rules[month]
            rows.append(
                {
                    "transaction_id": card_id(user.user_id, month, 990),
                    "user_id": user.user_id,
                    "approved_at": f"{month}-{day:02d}T{hour:02d}:18:00",
                    "merchant_name": merchant,
                    "amount": amount,
                    "category": category,
                    "subcategory": subcategory,
                    "payment_method": "credit_card",
                    "status": "approved",
                    "is_recurring": "false",
                }
            )

    rows.sort(key=lambda row: (row["approved_at"], row["transaction_id"]))
    return rows


def monthly_card_totals(card_rows: list[dict[str, object]], user_id: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in card_rows:
        if row["user_id"] != user_id:
            continue
        month = str(row["approved_at"])[:7]
        totals[month] = totals.get(month, 0) + int(row["amount"])
    return totals


def generate_account_transactions(user: UserSeed, card_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    balance = user.opening_balance
    card_totals = monthly_card_totals(card_rows, user.user_id)

    for month in MONTHS:
        sequence = 1
        entries: list[tuple[str, str, int, str, str, int]] = [
            (f"{month}-{user.pay_day:02d}T09:00:00", "in", user.job.replace("_", " ").title(), user.monthly_income, "income", "salary"),
            (f"{month}-{min(user.pay_day + 1, month_last_day(month)):02d}T09:10:00", "out", "Home Owner", user.rent, "fixed_cost", "rent"),
            (f"{month}-{min(user.pay_day + 2, month_last_day(month)):02d}T10:10:00", "out", "Mobile Carrier", user.telecom, "fixed_cost", "telecom"),
            (f"{month}-{min(user.pay_day + 3, month_last_day(month)):02d}T08:40:00", "out", "Utility Office", user.utility, "fixed_cost", "utility"),
        ]
        if user.insurance:
            entries.append(
                (
                    f"{month}-{min(user.pay_day + 4, month_last_day(month)):02d}T09:20:00",
                    "out",
                    "Insurance Co",
                    user.insurance,
                    "fixed_cost",
                    "insurance",
                )
            )
        if month in user.side_income_months:
            subcategory, amount = user.side_income_months[month]
            entries.append(
                (
                    f"{month}-{max(3, user.pay_day - 10):02d}T13:20:00",
                    "in",
                    "Additional Income",
                    amount,
                    "income",
                    subcategory,
                )
            )
        entries.append(
            (
                f"{month}-{month_last_day(month):02d}T09:05:00",
                "out",
                "Main Card",
                card_totals.get(month, 0),
                "card_bill",
                "card_payment",
            )
        )

        for transacted_at, tx_type, counterparty, amount, category, subcategory in sorted(entries):
            balance = balance + amount if tx_type == "in" else balance - amount
            rows.append(
                {
                    "transaction_id": account_id(user.user_id, month, sequence),
                    "user_id": user.user_id,
                    "transacted_at": transacted_at,
                    "type": tx_type,
                    "counterparty": counterparty,
                    "amount": amount,
                    "category": category,
                    "subcategory": subcategory,
                    "balance_after": balance,
                }
            )
            sequence += 1

    return rows


def write_user_profiles() -> None:
    payload = [
        {
            "user_id": user.user_id,
            "name": user.name,
            "age": user.age,
            "job": user.job,
            "monthly_income": user.monthly_income,
            "pay_day": user.pay_day,
            "residence_type": user.residence_type,
            "main_bank": user.main_bank,
            "main_card_type": user.main_card_type,
        }
        for user in USERS
    ]
    USER_PROFILE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path.name}")
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    write_user_profiles()
    all_card_rows: list[dict[str, object]] = []
    for user in USERS:
        all_card_rows.extend(generate_card_transactions(user))
    all_card_rows.sort(key=lambda row: (row["approved_at"], row["transaction_id"]))
    write_csv(CARD_TRANSACTIONS_PATH, all_card_rows)

    all_account_rows: list[dict[str, object]] = []
    for user in USERS:
        all_account_rows.extend(generate_account_transactions(user, all_card_rows))
    all_account_rows.sort(key=lambda row: (row["transacted_at"], row["transaction_id"]))
    write_csv(ACCOUNT_TRANSACTIONS_PATH, all_account_rows)

    print(f"users={len(USERS)} cards={len(all_card_rows)} accounts={len(all_account_rows)}")


if __name__ == "__main__":
    main()
