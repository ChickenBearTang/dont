"""Spring 금융 테이블용 가상 사용자 12명과 그 계좌·카드·거래 시드.

!! 전부 가짜다 !!
    실제 사람·거래가 아니다. 숫자는 '이런 형편의 사람이 있다면'이라는 가정이고, 20~30대 평균이나
    통계에 맞춘 값이 아니다. 목적은 구매 평가 흐름(재무 모델 + 5·3·2 예산 규칙)이 여러 형편과
    경계 사례에서 어떻게 움직이는지 끝까지 돌려 보는 것이다.

사용자는 무작위로 뽑지 않고 한 명씩 손으로 정했다 (PROFILES). 무작위는 개별 카드 거래의 날짜·가맹점·
금액에만 쓰고, 합계는 정해 둔 값에 정확히 맞춘다. 그래서 '이 사람은 130,000원짜리를 사면 빠듯함'
같은 기대값(expected_budget)이 데이터에서 그대로 나온다. 기대값이 맞는지는
tests/test_demo_db.py 가 실제 5·3·2 규칙 코드로 확인한다.

소득과 고정지출은 Spring DB 에 컬럼이 없다. 여기서는 계좌 거래(급여 입금, 월세·공과금·통신비·보험·
자동저축 출금)로 남겨 두어서 거래 내역에서 거꾸로 계산할 수 있게 했다. 투자·적금 이체는 5·3·2 의
생활비(5) 구역이 아니라서 고정지출에 넣지 않는다.

날짜는 모두 as_of(기준일) 에서 거꾸로 센 절대 날짜다. Spring 이 LocalDate.now() 로 최근 30일·이번 달을
계산하므로, 시드를 오래 두면 낡는다. 쓸 때 기준일을 오늘로 다시 만든다 (demo.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
import math
import random
from typing import Iterable, Sequence

from .sqlfmt import Raw, insert_rows, lit, quote

DEMO_EMAIL_DOMAIN = "demo.invalid"  # RFC 6761 예약 도메인: 실제로 존재하지 않는다
DEMO_COHORT_CODE = "DEMO"
DEMO_COHORT_GENERATION = 9999
DEMO_PASSWORD = "demo-pass-1234"
# 위 비밀번호의 BCrypt 해시 (Spring 의 BCryptPasswordEncoder 가 검증한다). tests 가 일치를 확인한다.
DEMO_PASSWORD_BCRYPT = "$2b$10$DemoDemoDemoDemoDemoDe6U/fR9Xx55r/TDVHZAYYIPBJdaTAh9q"

CARD_RANGE_DAYS = 180  # 카드 거래를 만드는 기간 (30일 블록 6개)
ACCOUNT_RANGE_DAYS = 120  # 계좌 거래를 만드는 기간
CARD_BLOCK_DAYS = 30
BANK_CODE = "999"
BANK_NAME = "데모은행"
TYPICAL_PRICE = 130_000  # 기대 예산 상태를 정할 때 쓴 기준 가격(마우스·키보드 정도)


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    persona: str  # finance_engine/personas.py 의 유형 이름과 같은 이름
    birth_date: date
    income: int  # 월 실수령
    rent: int
    other_fixed: int  # 통신비 + 공과금 + 보험
    savings: int  # 세이브박스 월 자동저축 (고정지출에 포함)
    spend_30d: int  # 최근 30일 카드 사용액 (정확히 이 값)
    tx_30d: int  # 최근 30일 카드 거래 건수
    primary_balance: int  # 연결계좌 잔액 목표(하한). 월 중 바닥을 메우느라 더 클 수 있다
    savebox_balance: int | None  # None 이면 세이브박스 없음
    has_card: bool = True
    has_accounts: bool = True
    pay_day: int = 25
    rent_day: int = 1
    card_day: int = 14  # 카드 결제일
    expected_budget: str = ""  # TYPICAL_PRICE 를 살 때 기대하는 5·3·2 상태
    notes: str = ""

    @property
    def fixed_expense(self) -> int:
        return self.rent + self.other_fixed + self.savings

    @property
    def email(self) -> str:
        return f"demo-{self.key}@{DEMO_EMAIL_DOMAIN}"

    @property
    def primary_account_no(self) -> str:
        return f"DEMO-{self.key}-P"

    @property
    def savebox_account_no(self) -> str:
        return f"DEMO-{self.key}-S"

    @property
    def card_no(self) -> str:
        return f"DEMO-CARD-{self.key}"


def _d(year: int, month: int, day: int) -> date:
    return date(year, month, day)


PROFILES: tuple[Profile, ...] = (
    Profile(
        "d01", "사회초년생 · 한도 여유 · 비상금 얇음", "사회초년생", _d(2002, 3, 14),
        income=2_500_000, rent=400_000, other_fixed=100_000, savings=100_000,
        spend_30d=200_000, tx_30d=26, primary_balance=900_000, savebox_balance=1_200_000,
        pay_day=25, rent_day=1, card_day=14, expected_budget="within",
        notes="사용량 32% → 130,000원 구매 후 74%. 비상금은 사용량의 1.5개월치라 EMERGENCY_COVER_LOW.",
    ),
    Profile(
        "d02", "사회초년생 · 빠듯함", "사회초년생", _d(2001, 8, 2),
        income=2_200_000, rent=450_000, other_fixed=120_000, savings=50_000,
        spend_30d=280_000, tx_30d=31, primary_balance=700_000, savebox_balance=900_000,
        pay_day=10, rent_day=5, card_day=25, expected_budget="tight",
        notes="구매 후 사용률 93.6% → TIGHT(WAIT).",
    ),
    Profile(
        "d03", "20대 후반 직장인 · 여유", "20대후반_직장인", _d(1998, 11, 21),
        income=3_200_000, rent=550_000, other_fixed=150_000, savings=200_000,
        spend_30d=300_000, tx_30d=34, primary_balance=1_800_000, savebox_balance=4_000_000,
        pay_day=25, rent_day=1, card_day=15, expected_budget="within",
        notes="사용량 37.5% → 구매 후 83%.",
    ),
    Profile(
        "d04", "20대 후반 직장인 · 이번 구매로 한도 초과", "20대후반_직장인", _d(1997, 6, 9),
        income=3_000_000, rent=600_000, other_fixed=150_000, savings=150_000,
        spend_30d=500_000, tx_30d=38, primary_balance=1_100_000, savebox_balance=2_500_000,
        pay_day=20, rent_day=3, card_day=10, expected_budget="over",
        notes="구매 전 93%(한도 안) → 구매 후 102%.",
    ),
    Profile(
        "d05", "30대 초반 · 여유 · 비상금 충분", "30대초반", _d(1994, 1, 30),
        income=4_500_000, rent=700_000, other_fixed=200_000, savings=300_000,
        spend_30d=450_000, tx_30d=40, primary_balance=3_200_000, savebox_balance=9_000_000,
        pay_day=25, rent_day=1, card_day=20, expected_budget="within",
        notes="구매 후 79%, 비상금 5.5개월치.",
    ),
    Profile(
        "d06", "30대 초반 · 이미 한도 초과", "30대초반", _d(1993, 9, 17),
        income=3_800_000, rent=800_000, other_fixed=250_000, savings=100_000,
        spend_30d=850_000, tx_30d=47, primary_balance=1_500_000, savebox_balance=1_500_000,
        pay_day=25, rent_day=2, card_day=15, expected_budget="already_over",
        notes="구매 전 사용률이 이미 105% → ALREADY_OVER.",
    ),
    Profile(
        "d07", "30대 후반 가구 · 보통", "30대후반_가구", _d(1988, 5, 6),
        income=5_500_000, rent=900_000, other_fixed=450_000, savings=300_000,
        spend_30d=600_000, tx_30d=44, primary_balance=4_200_000, savebox_balance=7_500_000,
        pay_day=25, rent_day=1, card_day=5, expected_budget="within",
        notes="구매 후 86.5%.",
    ),
    Profile(
        "d08", "30대 후반 가구 · 비상금 거의 없음", "30대후반_가구", _d(1989, 12, 3),
        income=5_000_000, rent=850_000, other_fixed=400_000, savings=0,
        spend_30d=700_000, tx_30d=42, primary_balance=1_900_000, savebox_balance=800_000,
        pay_day=25, rent_day=1, card_day=25, expected_budget="within",
        notes="한도는 여유(83%)인데 비상금이 사용량의 0.4개월치 → 재무 위험이 높게 나와야 하는 사례.",
    ),
    Profile(
        "d09", "경계 · 카드 없음", "20대후반_직장인", _d(1999, 2, 11),
        income=2_800_000, rent=500_000, other_fixed=100_000, savings=100_000,
        spend_30d=0, tx_30d=0, primary_balance=1_500_000, savebox_balance=1_000_000,
        has_card=False, pay_day=25, rent_day=1, card_day=14, expected_budget="unavailable",
        notes="카드·카드 거래가 없다 → 최근 거래가 없어 월 지출을 계산할 수 없음(예산 판단 안 함), 결제일은 기본 14일.",
    ),
    Profile(
        "d10", "경계 · 세이브박스 없음", "사회초년생", _d(2000, 4, 25),
        income=2_600_000, rent=500_000, other_fixed=100_000, savings=0,
        spend_30d=400_000, tx_30d=33, primary_balance=1_300_000, savebox_balance=None,
        pay_day=25, rent_day=1, card_day=14, expected_budget="within",
        notes="세이브박스 계좌 없음 → 비상금 0원. 구매 후 사용률 85%.",
    ),
    Profile(
        "d11", "경계 · 최근 거래 50건 초과(잘림)", "20대후반_직장인", _d(1998, 7, 8),
        income=3_400_000, rent=600_000, other_fixed=150_000, savings=150_000,
        spend_30d=700_000, tx_30d=80, primary_balance=1_400_000, savebox_balance=3_000_000,
        pay_day=25, rent_day=1, card_day=14, expected_budget="over",
        notes="최근 30일 80건 → Spring 이 보내는 최근 50건만으로는 월 지출을 낮게 잡는다(하한값, SPENDING_TRUNCATED).",
    ),
    Profile(
        "d12", "경계 · 계좌·카드 모두 없는 신규 가입", "사회초년생", _d(2003, 10, 19),
        income=0, rent=0, other_fixed=0, savings=0,
        spend_30d=0, tx_30d=0, primary_balance=0, savebox_balance=None,
        has_card=False, has_accounts=False, expected_budget="unavailable",
        notes="금융 정보가 전혀 없다 → 잔액 0, 결제일 기본 14일.",
    ),
)

# 카테고리 이름은 CardTransactionRepository 의 코호트 평균 쿼리가 쓰는 이름과 같다.
# (가중치, 중앙값(원), 로그 표준편차, 가맹점)
CATEGORIES: dict[str, tuple[float, int, float, tuple[str, ...]]] = {
    "식사/외식": (0.30, 11_000, 0.40, ("동네 국밥집", "역 앞 분식", "점심 백반집", "저녁 고깃집", "배달 주문")),
    "카페/간식": (0.19, 5_500, 0.35, ("동네 카페", "베이커리", "디저트 가게", "편의점 음료")),
    "쇼핑/마트": (0.14, 24_000, 0.55, ("동네 마트", "대형마트", "편의점")),
    "문화/여가": (0.07, 17_000, 0.45, ("영화관", "보드게임 카페", "전시관")),
    "의료/건강": (0.04, 14_000, 0.45, ("동네 약국", "의원")),
    "교통": (0.14, 1_600, 0.30, ("지하철", "버스", "교통카드 충전")),
    "쇼핑/온라인": (0.12, 32_000, 0.60, ("온라인 쇼핑몰", "온라인 서점", "온라인 패션몰")),
}


@dataclass(frozen=True)
class CardTx:
    on: date
    at: time
    merchant: str
    category: str
    amount: int
    approval_no: str


@dataclass(frozen=True)
class AccountEvent:
    on: date
    at: time
    account: str  # "P" | "S"
    signed: int  # 입금 +, 출금 -
    summary: str
    counter_account: str | None = None
    memo: str | None = None
    auto_savings_processed: bool = False


@dataclass
class UserSeed:
    profile: Profile
    start_day: date
    as_of: date
    card_tx: list[CardTx] = field(default_factory=list)
    # 계산이 끝난 계좌 거래: (account "P"/"S", seq, event, after_balance)
    account_rows: list[tuple[str, int, AccountEvent, int]] = field(default_factory=list)
    final_balance: dict[str, int] = field(default_factory=dict)


def _round(value: float, unit: int) -> int:
    return int(round(value / unit)) * unit


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _add_months(d: date, months: int) -> date:
    index = d.year * 12 + (d.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def _safe_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, 28))


def make_card_transactions(profile: Profile, as_of: date, rng: random.Random) -> list[CardTx]:
    """30일 블록 6개. 가장 최근 블록의 합계는 profile.spend_30d 와 정확히 같다."""
    if not profile.has_card:
        return []
    names = list(CATEGORIES)
    weights = [CATEGORIES[name][0] for name in names]
    result: list[CardTx] = []
    for block in range(CARD_RANGE_DAYS // CARD_BLOCK_DAYS):
        if block == 0:
            target = profile.spend_30d
            count = profile.tx_30d
        else:
            target = _round(profile.spend_30d * rng.uniform(0.85, 1.15), 100)
            count = max(8, round(profile.tx_30d * rng.uniform(0.85, 1.15)))
        picks: list[tuple[date, time, str, str, float]] = []
        for _ in range(count):
            category = rng.choices(names, weights)[0]
            _, median, sigma, merchants = CATEGORIES[category]
            raw = median * math.exp(sigma * rng.gauss(0, 1))
            day_offset = block * CARD_BLOCK_DAYS + rng.randrange(CARD_BLOCK_DAYS)
            seconds = rng.randrange(7 * 3600, 23 * 3600 + 1800)
            when = time(seconds // 3600, seconds % 3600 // 60, seconds % 60)
            picks.append((as_of - timedelta(days=day_offset), when, rng.choice(merchants), category, raw))
        raw_total = sum(p[4] for p in picks)
        amounts = [max(1_000, _round(p[4] * target / raw_total, 100)) for p in picks]
        residual = target - sum(amounts)
        biggest = max(range(len(amounts)), key=amounts.__getitem__)
        amounts[biggest] += residual
        if amounts[biggest] < 1_000:
            raise ValueError(f"{profile.key}: 카드 거래 합계를 맞출 수 없다 (block {block})")
        for (on, when, merchant, category, _), amount in zip(picks, amounts):
            result.append(
                CardTx(
                    on=on,
                    at=when,
                    merchant=merchant,
                    category=category,
                    amount=amount,
                    approval_no=f"{rng.randrange(10**8):08d}",
                )
            )
    result.sort(key=lambda t: (t.on, t.at))
    return result


def _fixed_breakdown(other_fixed: int) -> list[tuple[str, int, int]]:
    """other_fixed 를 (이름, 일, 금액) 으로 쪼갠다. 합이 정확히 other_fixed 다."""
    if other_fixed <= 0:
        return []
    phone = min(55_000, other_fixed)
    rest = other_fixed - phone
    utilities = _round(rest * 0.6, 1_000) if rest else 0
    insurance = rest - utilities
    items = [("통신비", 15, phone)]
    if utilities:
        items.append(("관리비·공과금", 20, utilities))
    if insurance:
        items.append(("보험료", 10, insurance))
    return items


def make_account_events(profile: Profile, as_of: date, card_tx: Sequence[CardTx], start_day: date) -> list[AccountEvent]:
    """급여·고정지출·자동저축·투자 이체·카드대금 출금 (이월 입금은 따로 붙인다)."""
    if not profile.has_accounts:
        return []
    events: list[AccountEvent] = []
    has_savebox = profile.savebox_balance is not None
    invest = max(0, _round(profile.income - profile.fixed_expense - profile.spend_30d - profile.income * 0.03, 10_000))
    card_start = as_of - timedelta(days=CARD_RANGE_DAYS - 1)
    first = _month_start(start_day)
    month = first
    while month <= as_of:
        y, m = month.year, month.month

        def at(day: int) -> date:
            return _safe_day(y, m, day)

        def add(day: int, minute: int, signed: int, summary: str, **kw) -> None:
            on = at(day)
            if start_day <= on <= as_of and signed != 0:
                events.append(AccountEvent(on=on, at=time(9, minute), account=kw.pop("account", "P"), signed=signed, summary=summary, **kw))

        add(profile.pay_day, 0, profile.income, "급여 입금", memo="DEMO 급여", auto_savings_processed=has_savebox and profile.savings > 0)
        if has_savebox and profile.savings > 0:
            add(profile.pay_day, 1, -profile.savings, "(자동저축) 출금", counter_account=profile.savebox_account_no)
            add(profile.pay_day, 1, profile.savings, "(자동저축) 입금", account="S", counter_account=profile.primary_account_no)
        add(profile.rent_day, 0, -profile.rent, "월세")
        for name, day, amount in _fixed_breakdown(profile.other_fixed):
            add(day, 0, -amount, name)
        add(min(profile.pay_day + 1, 28), 0, -invest, "정기 이체(적금·투자)")

        if profile.has_card:
            prev = _add_months(month, -1)
            prev_end = month - timedelta(days=1)
            if prev >= card_start:
                bill = sum(t.amount for t in card_tx if prev <= t.on <= prev_end)
                add(profile.card_day, 30, -bill, "카드대금 출금", counter_account=profile.card_no)
        month = _add_months(month, 1)
    return events


def build_user(profile: Profile, as_of: date, seed: int) -> UserSeed:
    rng = random.Random(f"{seed}:{profile.key}")
    start_day = as_of - timedelta(days=ACCOUNT_RANGE_DAYS - 1)
    user = UserSeed(profile=profile, start_day=start_day, as_of=as_of)
    user.card_tx = make_card_transactions(profile, as_of, rng)
    if not profile.has_accounts:
        return user

    events = make_account_events(profile, as_of, user.card_tx, start_day)
    targets = {"P": profile.primary_balance}
    if profile.savebox_balance is not None:
        targets["S"] = profile.savebox_balance
    for account, target in targets.items():
        mine = sorted((e for e in events if e.account == account), key=lambda e: (e.on, e.at))
        net = sum(e.signed for e in mine)
        # 잔액이 한 번도 음수가 되지 않게 하는 최소 시작 잔액. 월급 전에 월세·카드대금이 먼저 나가면
        # 월 중반에 바닥이 생긴다. 바닥을 메우려면 목표(target)보다 현재 잔액이 높아질 수 있다 —
        # 그래서 primary_balance 는 '이 정도 이상'이고, 실제 값은 데이터에서 읽는다.
        running, lowest = 0, 0
        for event in mine:
            running += event.signed
            lowest = min(lowest, running)
        opening = max(target - net, -lowest)
        if opening > 0:
            events.append(
                AccountEvent(
                    on=start_day, at=time(8, 0), account=account, signed=opening,
                    summary="(이월) 데모 시작 잔액", memo="DEMO 시작 잔액",
                )
            )

    for account in targets:
        running = 0
        seq = 0
        for event in sorted((e for e in events if e.account == account), key=lambda e: (e.on, e.at)):
            running += event.signed
            if running < 0:  # 위에서 막았으므로 일어나면 버그다
                raise AssertionError(f"{profile.key}/{account}: {event.on} 에 잔액이 음수({running:,})")
            seq += 1
            user.account_rows.append((account, seq, event, running))
        user.final_balance[account] = running
    return user


# ---------------------------------------------------------------- SQL 출력

USERS_SELECT = f"SELECT id FROM users WHERE email LIKE '%@{DEMO_EMAIL_DOMAIN}'"


def cleanup_sql() -> str:
    """이전에 넣은 데모 행만 지운다 (이메일 도메인으로 구분). 코호트는 남긴다."""
    return "\n".join(
        [
            f"DELETE FROM card_transactions WHERE user_id IN ({USERS_SELECT});",
            f"DELETE FROM cards WHERE user_id IN ({USERS_SELECT});",
            f"DELETE FROM account_transactions WHERE account_id IN (SELECT id FROM accounts WHERE user_id IN ({USERS_SELECT}));",
            f"DELETE FROM savings_settings WHERE user_id IN ({USERS_SELECT});",
            f"DELETE FROM accounts WHERE user_id IN ({USERS_SELECT});",
            f"DELETE FROM users WHERE email LIKE '%@{DEMO_EMAIL_DOMAIN}';",
        ]
    )


def _user_id(email: str) -> Raw:
    return Raw(f"(SELECT id FROM users WHERE email = {quote(email)})")


def _account_id(account_no: str) -> Raw:
    return Raw(f"(SELECT id FROM accounts WHERE account_no = {quote(account_no)})")


def seed_sql(as_of: date, seed: int, profiles: Iterable[Profile] = PROFILES) -> str:
    users = [build_user(p, as_of, seed) for p in profiles]
    created = datetime.combine(as_of - timedelta(days=CARD_RANGE_DAYS), time(9, 0))
    out: list[str] = [
        "-- 자동 생성 파일 (demo.py generate). 직접 고치지 말고 생성기를 고친다.",
        f"-- as_of={as_of.isoformat()} seed={seed}  — 전부 가짜 데이터다. 운영 DB 에 넣지 않는다.",
        "BEGIN;",
        cleanup_sql(),
        insert_rows(
            "cohorts",
            ["cohort_code", "generation_no", "start_date", "end_date", "created_at", "updated_at"],
            [[DEMO_COHORT_CODE, DEMO_COHORT_GENERATION, as_of - timedelta(days=365), as_of + timedelta(days=365), created, created]],
            suffix="ON CONFLICT (cohort_code) DO NOTHING",
        ),
    ]

    cohort_id = Raw(f"(SELECT id FROM cohorts WHERE cohort_code = {quote(DEMO_COHORT_CODE)})")
    out.append(
        insert_rows(
            "users",
            [
                "email", "password", "name", "birth_date", "nickname", "profile_image_url",
                "terms_agreed", "terms_agreed_at", "monthly_saving_goal_amount", "onboarding_status", "user_role",
                "status", "deleted_at", "cohort_id", "created_at", "updated_at",
            ],
            [
                [
                    u.profile.email, DEMO_PASSWORD_BCRYPT, f"데모사용자{u.profile.key[1:]}", u.profile.birth_date,
                    f"demo{u.profile.key[1:]}", None, True, created,
                    (u.profile.savings if u.profile.savings > 0 else None), "COMPLETED", "USER", "ACTIVE", None,
                    cohort_id, created, created,
                ]
                for u in users
            ],
        )
    )

    account_rows: list[list[object]] = []
    for u in users:
        p = u.profile
        if not p.has_accounts:
            continue
        for kind, account_no, role, primary, type_code, type_name, name in (
            ("P", p.primary_account_no, "LINKED_DEPOSIT", True, "1", "수시입출금", f"{p.key} 생활비 계좌"),
            ("S", p.savebox_account_no, "SAVE_BOX", False, "2", "세이브박스", f"{p.key} 세이브박스"),
        ):
            if kind not in u.final_balance:
                continue
            dates = [r[2].on for r in u.account_rows if r[0] == kind]
            account_rows.append(
                [
                    _user_id(p.email), account_no, BANK_CODE, BANK_NAME, role, primary, type_code, type_name, name,
                    u.start_day - timedelta(days=30), as_of + timedelta(days=1825), 5_000_000, 1_000_000,
                    u.final_balance[kind], max(dates), "KRW", "ACTIVE", f"데모사용자{p.key[1:]}", created, created,
                ]
            )
    out.append(
        insert_rows(
            "accounts",
            [
                "user_id", "account_no", "bank_code", "bank_name", "account_role", "is_primary", "account_type_code",
                "account_type_name", "account_name", "account_created_date", "account_expiry_date",
                "daily_transfer_limit", "one_time_transfer_limit", "balance", "last_transaction_date",
                "currency_code", "status", "user_name", "created_at", "updated_at",
            ],
            account_rows,
        )
    )

    tx_rows: list[list[object]] = []
    for u in users:
        for kind, seq, event, after in u.account_rows:
            account_no = u.profile.primary_account_no if kind == "P" else u.profile.savebox_account_no
            moment = datetime.combine(event.on, event.at)
            tx_rows.append(
                [
                    _account_id(account_no), f"DEMO-{u.profile.key}-{kind}-{seq:04d}", event.on,
                    event.at.strftime("%H%M%S"), "1" if event.signed > 0 else "2",
                    "입금" if event.signed > 0 else "출금(이체)", event.counter_account, abs(event.signed), after,
                    event.summary, event.memo, event.auto_savings_processed, moment,
                ]
            )
    out.append(
        insert_rows(
            "account_transactions",
            [
                "account_id", "transaction_unique_no", "transaction_date", "transaction_time", "transaction_type",
                "transaction_type_name", "transaction_account_no", "transaction_amount", "after_balance",
                "transaction_summary", "transaction_memo", "auto_savings_processed", "created_at",
            ],
            tx_rows,
        )
    )

    setting_rows = [
        [
            _user_id(u.profile.email), _account_id(u.profile.primary_account_no),
            _account_id(u.profile.savebox_account_no), "급여", u.profile.savings, True, created, created,
        ]
        for u in users
        if u.profile.has_accounts and u.profile.savebox_balance is not None and u.profile.savings > 0
    ]
    if setting_rows:
        out.append(
            insert_rows(
                "savings_settings",
                ["user_id", "primary_account_id", "savebox_account_id", "keyword", "savings_amount", "is_active", "created_at", "updated_at"],
                setting_rows,
            )
        )

    card_rows = [
        [
            _user_id(u.profile.email), u.profile.card_no, "000", f"DEMO-UNIQUE-{u.profile.key}", "DEMO", "데모카드",
            "데모 신용카드", "데모용 가상 카드", 300_000, 30_000, "203012", u.profile.primary_account_no,
            str(u.profile.card_day), created, created,
        ]
        for u in users
        if u.profile.has_card
    ]
    if card_rows:
        out.append(
            insert_rows(
                "cards",
                [
                    "user_id", "card_no", "cvc", "card_unique_no", "card_issuer_code", "card_issuer_name", "card_name",
                    "card_description", "baseline_performance", "max_benefit_limit", "card_expiry_date",
                    "withdrawal_account_no", "withdrawal_date", "created_at", "updated_at",
                ],
                card_rows,
            )
        )

    # card_transactions: 카드 번호로 cards 와 이어 붙여 card_id·user_id 를 채운다.
    tx_values: list[list[object]] = []
    for u in users:
        for t in u.card_tx:
            moment = datetime.combine(t.on, t.at)
            tx_values.append(
                [u.profile.card_no, t.on, t.at.strftime("%H%M%S"), t.merchant, t.category, t.amount, "승인", t.approval_no, moment]
            )
    for start in range(0, len(tx_values), 400):
        body = ",\n".join("    (" + ", ".join(lit(v) for v in row) + ")" for row in tx_values[start : start + 400])
        out.append(
            "INSERT INTO card_transactions (card_id, transaction_date, transaction_time, merchant_name, category_name, "
            "transaction_amount, transaction_type, approval_no, description, user_id, created_at, updated_at)\n"
            "SELECT c.id, v.d, v.t, v.m, v.cat, v.amt, v.ty, v.ap, NULL, c.user_id, v.ts, v.ts\n"
            f"FROM (VALUES\n{body}\n) AS v(card_no, d, t, m, cat, amt, ty, ap, ts)\n"
            "JOIN cards c ON c.card_no = v.card_no;"
        )

    out.append("COMMIT;")
    return "\n".join(out) + "\n"
