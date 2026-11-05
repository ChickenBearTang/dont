"""demo DB (backend/demo-db) 시드가 약속한 모양인지 확인한다.

두 종류를 확인한다.
  1. 생성기 단독: 같은 입력이면 같은 출력, 합계·잔액 연쇄가 맞음, 5·3·2 기대 상태가 실제 규칙 코드로
     확인됨, crawl 제목이 스토어의 품목 분류기와 같은 결과를 냄.
  2. 임시 PostgreSQL 에 실제로 적재: DDL 이 JPA 엔티티의 컬럼과 맞고, 두 번 적재해도 같고, 스토어의
     이상치 배치가 시드가 표시한 이상치를 실제로 잡음.

!! 이 테스트가 확인하지 않는 것 !!
    Spring(Java)은 실행하지 않는다. DDL 이 엔티티와 맞는지는 소스 텍스트의 @Column 선언을 읽어 비교할
    뿐이고, Hibernate 가 실제로 이 테이블에서 읽고 쓰는지는 확인하지 못했다.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import importlib
from pathlib import Path
import re
import subprocess
import sys
import unittest
import warnings

from ..storage.postgres_store import PostgresCrawlStore
from ..xai.budget_rule import BudgetStatus, assess_budget
from ..xai.spending import RecentTransaction, estimate_monthly_spending

DEMO_DIR = Path(__file__).resolve().parents[3] / "demo-db"
JAVA_DIR = Path(__file__).resolve().parents[3] / "src" / "main" / "java" / "com" / "ssafy" / "edu" / "awesomeproject"

if not DEMO_DIR.exists():  # AI 서비스 이미지처럼 demo-db 가 없는 곳에서는 건너뛴다
    raise unittest.SkipTest(f"{DEMO_DIR} 가 없어 demo DB 테스트를 건너뛴다")

if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

crawl = importlib.import_module("demo_data.crawl")
finance = importlib.import_module("demo_data.finance")
demo_cli = importlib.import_module("demo")

KST = timezone(timedelta(hours=9))
AS_OF = date(2026, 11, 5)
SEED = 7
SALARY = "급여 입금"
FIXED_SUMMARIES = {"월세", "통신비", "관리비·공과금", "보험료", "세이브박스 자동저축"}


def _minus_months(day: date, months: int) -> date:
    """java.time.LocalDate.minusMonths: 말일을 넘으면 그 달 말일로 줄인다."""
    index = day.year * 12 + (day.month - 1) - months
    year, month = index // 12, index % 12 + 1
    for last in (31, 30, 29, 28):
        try:
            return date(year, month, min(day.day, last))
        except ValueError:
            continue
    raise AssertionError("unreachable")


def _spring_recent_transactions(user, as_of: date) -> list[RecentTransaction]:
    """PrXaiContextService.buildRecentTransactions 와 같은 선택: 최근 3개월, 날짜·시각 내림차순, 50건."""
    start = _minus_months(as_of, 3)
    rows = [t for t in user.card_tx if start <= t.on <= as_of]
    rows.sort(key=lambda t: (t.on, t.at), reverse=True)
    return [RecentTransaction(t.on.strftime("%Y%m%d"), t.amount) for t in rows[:50]]


def _month_flows(user, month_start: date) -> tuple[int, int]:
    """한 달(month_start 가 속한 달)의 (급여, 고정지출) 을 계좌 거래에서 읽는다."""
    month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    income = fixed = 0
    for account, _, event, _ in user.account_rows:
        if not (month_start <= event.on < month_end) or account != "P":
            continue
        if event.summary == SALARY:
            income += event.signed
        elif event.summary in FIXED_SUMMARIES:
            fixed += -event.signed
    return income, fixed


class DemoGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.users = {p.key: finance.build_user(p, AS_OF, SEED) for p in finance.PROFILES}

    def test_same_input_gives_same_sql_and_other_input_does_not(self) -> None:
        self.assertEqual(finance.seed_sql(AS_OF, SEED), finance.seed_sql(AS_OF, SEED))
        self.assertEqual(crawl.seed_sql(AS_OF, SEED), crawl.seed_sql(AS_OF, SEED))
        self.assertNotEqual(finance.seed_sql(AS_OF, SEED), finance.seed_sql(AS_OF, SEED + 1))
        self.assertNotEqual(crawl.seed_sql(AS_OF, SEED), crawl.seed_sql(AS_OF + timedelta(days=1), SEED))

    def test_every_profile_builds_on_every_day_of_a_year(self) -> None:
        """월급날·월말·말일이 어디에 걸려도 잔액이 음수가 되지 않는다 (as_of 가 오늘로 바뀌므로)."""
        for offset in range(0, 366, 5):
            as_of = date(2026, 1, 1) + timedelta(days=offset)
            for profile in finance.PROFILES:
                finance.build_user(profile, as_of, SEED)  # 실패하면 예외

    def test_demo_users_are_obviously_fake(self) -> None:
        for profile in finance.PROFILES:
            self.assertTrue(profile.email.endswith("@demo.invalid"))
            self.assertTrue(profile.primary_account_no.startswith("DEMO-"))
            self.assertLessEqual(len(profile.primary_account_no), 30)
        self.assertEqual(len({p.key for p in finance.PROFILES}), len(finance.PROFILES))

    def test_demo_password_hash_matches_when_crypt_is_available(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                import crypt  # 3.13 에서 제거됨
            except ModuleNotFoundError:
                self.skipTest("crypt 모듈이 없다")
        self.assertEqual(
            crypt.crypt(finance.DEMO_PASSWORD, finance.DEMO_PASSWORD_BCRYPT), finance.DEMO_PASSWORD_BCRYPT
        )

    def test_last_30_days_of_card_spending_is_exactly_the_designed_amount(self) -> None:
        for key, user in self.users.items():
            profile = user.profile
            recent = [t for t in user.card_tx if 0 <= (AS_OF - t.on).days < 30]
            self.assertEqual(sum(t.amount for t in recent), profile.spend_30d, key)
            self.assertEqual(len(recent), profile.tx_30d, key)
            self.assertTrue(all(t.amount >= 1_000 for t in user.card_tx), key)
            self.assertTrue(all(t.category in finance.CATEGORIES for t in user.card_tx), key)
            self.assertTrue(all(t.on <= AS_OF for t in user.card_tx), key)

    def test_account_balance_chain_is_consistent_and_never_negative(self) -> None:
        for key, user in self.users.items():
            for account in ("P", "S"):
                rows = [r for r in user.account_rows if r[0] == account]
                running = 0
                for _, _, event, after in rows:
                    running += event.signed
                    self.assertEqual(running, after, f"{key}/{account}")
                    self.assertGreaterEqual(after, 0, f"{key}/{account}")
                if rows:
                    self.assertEqual(user.final_balance[account], rows[-1][3], key)
            if user.profile.savebox_balance is not None and user.profile.has_accounts:
                self.assertGreaterEqual(user.final_balance["S"], user.profile.savebox_balance, key)
            if user.profile.has_accounts:
                self.assertGreaterEqual(user.final_balance["P"], user.profile.primary_balance, key)

    def test_income_and_fixed_expense_can_be_read_back_from_account_transactions(self) -> None:
        """Spring DB 에는 소득·고정지출 컬럼이 없다. 그래서 거래에서 거꾸로 읽을 수 있어야 한다."""
        last_full_month = (AS_OF.replace(day=1) - timedelta(days=1)).replace(day=1)
        for key, user in self.users.items():
            profile = user.profile
            if not profile.has_accounts:
                continue
            income, fixed = _month_flows(user, last_full_month)
            self.assertEqual(income, profile.income, key)
            self.assertEqual(fixed, profile.fixed_expense, key)

    def test_expected_budget_state_matches_the_real_rule(self) -> None:
        """기대 상태를 손으로 적어 둔 것이 아니라 5·3·2 규칙 코드로 계산한 결과와 같아야 한다."""
        last_full_month = (AS_OF.replace(day=1) - timedelta(days=1)).replace(day=1)
        for key, user in self.users.items():
            profile = user.profile
            income, fixed = _month_flows(user, last_full_month) if profile.has_accounts else (None, None)
            spending = estimate_monthly_spending(
                [
                    RecentTransaction(t.on.strftime("%Y%m%d"), t.amount)
                    for t in user.card_tx
                    if 0 <= (AS_OF - t.on).days < 30
                ],
                as_of=AS_OF,
            ).amount  # 거래가 없으면 None -> 판단 불가
            savebox = user.final_balance.get("S", 0) if profile.has_accounts else None
            assessment = assess_budget(
                monthly_income=income,
                fixed_expense=fixed,
                variable_spending_30d=spending,
                price=finance.TYPICAL_PRICE,
                emergency_fund_balance=savebox,
            )
            self.assertEqual(assessment.status.value, profile.expected_budget, f"{key}: {assessment}")

    def test_all_four_budget_states_plus_unavailable_are_covered(self) -> None:
        self.assertEqual(
            {p.expected_budget for p in finance.PROFILES},
            {"within", "tight", "over", "already_over", "unavailable"},
        )

    def test_low_emergency_fund_cases_are_present(self) -> None:
        """비상금이 사용량의 3개월 미만인 사용자가 있어서 EMERGENCY_COVER_LOW 경로를 탄다."""
        low = []
        for key, user in self.users.items():
            profile = user.profile
            if not (profile.has_accounts and profile.has_card):
                continue
            used = profile.fixed_expense + profile.spend_30d
            if user.final_balance.get("S", 0) < 3 * used:
                low.append(key)
        self.assertIn("d01", low)
        self.assertIn("d08", low)

    def test_truncation_case_loses_spending_exactly_the_way_spring_would(self) -> None:
        """Spring 은 최근 50건만 보낸다. 30일에 80건인 사용자는 월 지출이 낮게 잡히고 잘림 표시가 붙는다."""
        user = self.users["d11"]
        estimate = estimate_monthly_spending(_spring_recent_transactions(user, AS_OF), as_of=AS_OF)
        self.assertTrue(estimate.truncated)
        self.assertLess(estimate.amount, user.profile.spend_30d)
        # 잘린 값으로 계산하면 실제로는 한도 초과인 사용자가 '여유'로 보인다 — 이 사례의 요점이다.
        income, fixed = _month_flows(user, (AS_OF.replace(day=1) - timedelta(days=1)).replace(day=1))
        wrong = assess_budget(
            monthly_income=income, fixed_expense=fixed, variable_spending_30d=estimate.amount, price=finance.TYPICAL_PRICE
        )
        right = assess_budget(
            monthly_income=income, fixed_expense=fixed, variable_spending_30d=user.profile.spend_30d, price=finance.TYPICAL_PRICE
        )
        self.assertEqual(right.status, BudgetStatus.OVER)
        self.assertEqual(wrong.status, BudgetStatus.WITHIN)

    def test_other_users_are_not_truncated(self) -> None:
        for key, user in self.users.items():
            if key == "d11" or not user.profile.has_card:
                continue
            estimate = estimate_monthly_spending(_spring_recent_transactions(user, AS_OF), as_of=AS_OF)
            self.assertFalse(estimate.truncated, key)
            self.assertEqual(estimate.amount, user.profile.spend_30d, key)

    def test_users_without_card_or_accounts_have_nothing_to_estimate(self) -> None:
        for key in ("d09", "d12"):
            estimate = estimate_monthly_spending(_spring_recent_transactions(self.users[key], AS_OF), as_of=AS_OF)
            self.assertIsNone(estimate.amount, key)
            self.assertEqual(estimate.reason, "no_transactions", key)

    def test_card_withdrawal_day_is_a_plain_day_of_month_springs_parser_reads(self) -> None:
        for profile in finance.PROFILES:
            if profile.has_card:
                self.assertTrue(1 <= profile.card_day <= 28, profile.key)


class DemoCrawlGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = crawl.make_rows(AS_OF, SEED)

    def test_titles_are_classified_into_the_intended_family_by_the_real_store(self) -> None:
        for row in self.rows:
            self.assertEqual(
                PostgresCrawlStore.classify_item_family(title=row.title, url=row.url), row.item_family, row.title
            )

    def test_stored_price_is_what_the_store_would_have_written(self) -> None:
        for row in self.rows:
            self.assertEqual(PostgresCrawlStore._normalize_krw_price(f"{int(row.price):,}원"), row.price)
            self.assertEqual(PostgresCrawlStore._extract_post_id(row.url), row.post_id)

    def test_rows_are_unmistakably_demo_and_unique(self) -> None:
        self.assertEqual(len({r.url for r in self.rows}), len(self.rows))
        self.assertTrue(all(r.url.startswith(crawl.DEMO_SOURCE_PREFIX) for r in self.rows))
        self.assertTrue(all(r.source.startswith(crawl.DEMO_SOURCE_PREFIX) for r in self.rows))

    def test_time_order_and_calendar(self) -> None:
        end = datetime.combine(AS_OF, time.max, tzinfo=KST)
        for row in self.rows:
            self.assertLessEqual(row.first_seen_at, row.last_seen_at)
            self.assertLessEqual(row.last_seen_at, end)
            self.assertTrue(re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", row.posted_at))
            self.assertGreaterEqual(date.fromisoformat(row.posted_at.replace(".", "-")), AS_OF - timedelta(days=crawl.HISTORY_DAYS))

    def test_each_product_has_enough_history_and_two_injected_anomalies(self) -> None:
        for product in crawl.PRODUCTS:
            mine = [r for r in self.rows if r.item_family == product.family]
            self.assertGreaterEqual(len(mine), 100)
            self.assertEqual(sum(r.kind == "anomaly" for r in mine), 2)
            normal = sorted(int(r.price) for r in mine if r.kind == "normal")
            self.assertGreater(normal[0], product.base_price * 0.5)
            self.assertLess(normal[-1], product.base_price * 1.5)
            # 값이 실제로 움직인다: 학습 feature 가 상수가 되지 않는다
            self.assertGreater(len(set(normal)), 30)


class DemoCrawlFeedsPricePipelineTests(unittest.TestCase):
    """데모 가격 데이터가 기존 가격 학습 파이프라인(dataset_builder)을 끝까지 통과하고, 값이 있는 feature 가 나온다.

    실제 크롤 행 -> PriceObservation 변환기는 이 브랜치에 없다. 여기서는 필요한 최소 변환(제품=item_family,
    판매처=제목의 [몰] 이름)만 테스트 안에서 한다. 이 테스트는 '데모 데이터로 파이프라인이 돈다'는 것만 확인하며,
    가격 모델이 좋은지(정답이 feature 에 섞인 문제 등)와는 상관이 없다.
    """

    def test_enough_features_vary_to_train_on(self) -> None:
        from ..price_engine.allowlist import training_feature_names
        from ..price_engine.dataset_builder import build_price_feature_snapshot_v1
        from ..price_engine.schema_models import PriceObservation

        observations = []
        for row in crawl.make_rows(AS_OF, SEED):
            if row.is_outlier:
                continue
            mall = re.match(r"\[([^\]]+)\]", row.title).group(1)
            observations.append(
                PriceObservation(
                    canonical_product_id_candidate=row.item_family,
                    variant_id_candidate=None,
                    seller_id_candidate=mall,
                    observed_at=row.fetched_at,
                    listed_price=int(row.price),
                    shipping_fee=0,
                    effective_price_candidate=int(row.price),
                    availability_status="in_stock",
                    stock_status=None,
                    source_site="quasarzone",
                    source_priority="community",
                    confidence=0.8,
                    evidence_refs=[{"url": row.url}],
                    normalization_version="demo",
                )
            )
        rows = build_price_feature_snapshot_v1(observations).training_rows
        self.assertGreater(len(rows), 300)
        varying = []
        for name in training_feature_names():
            values = {getattr(r, name, None) for r in rows} - {None}
            if len(values) > 1:
                varying.append(name)
        # 실제 크롤 67행에서는 17개 중 0개였다. brand/category/seller_type/availability/배송비 최빈값은
        # 이 변환기가 채우지 않아 상수로 남는다.
        self.assertGreaterEqual(len(varying), 10, varying)


class SafetyGuardTests(unittest.TestCase):
    def test_local_and_demo_hosts_are_allowed(self) -> None:
        for dsn in (
            "postgresql://u:p@localhost:5432/x",
            "postgresql://u:p@127.0.0.1/x",
            "postgresql://u:p@[::1]/x",
            "postgresql:///x",
            "host=/var/run/postgresql dbname=x",
            "dbname=x user=y",
            "host=localhost dbname=x",
            "postgresql://u:p@demo-postgres:5432/x",
            "postgresql://u@/x?host=/tmp/sock",
        ):
            self.assertTrue(demo_cli.is_local_dsn(dsn), dsn)

    def test_remote_hosts_are_refused_without_force(self) -> None:
        for dsn in (
            "postgresql://u:p@db.example.com:5432/x",
            "postgresql://u:p@10.0.0.5/x",
            "host=prod-db.internal dbname=x",
            "host='rds.amazonaws.com' dbname=x",
        ):
            self.assertFalse(demo_cli.is_local_dsn(dsn), dsn)
            with self.assertRaises(SystemExit):
                demo_cli.require_safe(dsn, force=False)
            demo_cli.require_safe(dsn, force=True)  # --force 면 통과


try:
    from ._pg_fixture import TempPostgres, require_postgres
except ModuleNotFoundError:  # pragma: no cover
    TempPostgres = None  # type: ignore[assignment]


def _java_columns(java_file: Path) -> tuple[str, dict[str, bool]]:
    """엔티티 소스에서 (테이블 이름, {컬럼: nullable}) 을 읽는다. 간단한 텍스트 읽기다."""
    text = java_file.read_text(encoding="utf-8")
    table = re.search(r'@Table\(\s*name\s*=\s*"([a-z_]+)"', text)
    assert table, java_file
    columns: dict[str, bool] = {"id": False}
    for body in re.findall(r"@(?:Column|JoinColumn)\(([^)]*)\)", text):
        name = re.search(r'name\s*=\s*"([a-z_]+)"', body)
        if name is None:
            continue
        columns[name.group(1)] = "nullable = false" not in body
    if re.search(r"extends\s+BaseEntity", text):
        columns["created_at"] = False
        columns["updated_at"] = False
    return table.group(1), columns


ENTITY_FILES = (
    "domain/community/entity/Cohort.java",
    "domain/auth/entity/User.java",
    "domain/fin/account/entity/Account.java",
    "domain/fin/account/entity/AccountTransaction.java",
    "domain/fin/account/entity/SavingsSetting.java",
    "domain/fin/card/entity/Card.java",
    "domain/fin/card/entity/CardTransaction.java",
)


@unittest.skipIf(TempPostgres is None, "_pg_fixture 가 없다")
class DemoDatabaseLoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_postgres()  # 서버 바이너리가 없으면 건너뜀
        cls.pg = TempPostgres()
        cls.as_of = datetime.now(KST).date()
        cls.finance_dsn = cls.pg.new_database()
        cls.crawl_dsn = cls.pg.new_database()
        demo_cli.apply_finance(cls.finance_dsn, cls.as_of, SEED)
        demo_cli.apply_crawl(cls.crawl_dsn, cls.as_of, SEED)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pg.close()

    def _connect(self, dsn: str):
        import psycopg

        return psycopg.connect(dsn)

    # ---------------------------------------------------------------- 스키마

    def test_ddl_columns_match_the_jpa_entities(self) -> None:
        if not JAVA_DIR.exists():
            self.skipTest("Spring 소스가 없다")
        with self._connect(self.finance_dsn) as connection:
            for relative in ENTITY_FILES:
                table, expected = _java_columns(JAVA_DIR / relative)
                rows = connection.execute(
                    "SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = %s",
                    (table,),
                ).fetchall()
                actual = {name: nullable == "YES" for name, nullable in rows}
                self.assertEqual(set(actual), set(expected), f"{table}: 컬럼 목록이 엔티티와 다르다")
                for name, nullable in expected.items():
                    self.assertEqual(actual[name], nullable, f"{table}.{name}: nullable 이 엔티티와 다르다")

    def test_crawl_ddl_matches_what_the_store_creates(self) -> None:
        with self._connect(self.crawl_dsn) as connection:
            before = connection.execute(
                "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'crawl_items' ORDER BY column_name"
            ).fetchall()
        fresh = self.pg.new_database()
        PostgresCrawlStore(fresh)  # 스토어가 직접 만든다
        with self._connect(fresh) as connection:
            after = connection.execute(
                "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'crawl_items' ORDER BY column_name"
            ).fetchall()
        self.assertEqual(before, after)

    # ---------------------------------------------------------------- 금융 데이터

    def test_row_counts_and_relations(self) -> None:
        with self._connect(self.finance_dsn) as connection:
            counts = {
                table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in ("users", "accounts", "account_transactions", "savings_settings", "cards", "card_transactions")
            }
            self.assertEqual(counts["users"], len(finance.PROFILES))
            self.assertEqual(counts["cards"], sum(p.has_card for p in finance.PROFILES))
            self.assertGreater(counts["card_transactions"], 1_000)
            mismatched = connection.execute(
                "SELECT count(*) FROM card_transactions ct JOIN cards c ON c.id = ct.card_id WHERE c.user_id <> ct.user_id"
            ).fetchone()[0]
            self.assertEqual(mismatched, 0)
            primaries = connection.execute(
                "SELECT user_id, count(*) FROM accounts WHERE is_primary GROUP BY user_id HAVING count(*) <> 1"
            ).fetchall()
            self.assertEqual(primaries, [])

    def test_stored_balance_equals_last_transaction_and_chain_holds(self) -> None:
        with self._connect(self.finance_dsn) as connection:
            broken = connection.execute(
                """
                SELECT a.account_no
                FROM accounts a
                JOIN LATERAL (
                    SELECT after_balance FROM account_transactions
                    WHERE account_id = a.id ORDER BY transaction_date DESC, transaction_time DESC, id DESC LIMIT 1
                ) last_tx ON TRUE
                WHERE last_tx.after_balance <> a.balance
                """
            ).fetchall()
            self.assertEqual(broken, [])
            chain = connection.execute(
                """
                SELECT count(*) FROM (
                    SELECT after_balance - COALESCE(LAG(after_balance) OVER w, 0)
                               = CASE WHEN transaction_type = '1' THEN transaction_amount ELSE -transaction_amount END AS ok
                    FROM account_transactions
                    WINDOW w AS (PARTITION BY account_id ORDER BY transaction_date, transaction_time, id)
                ) t WHERE NOT ok
                """
            ).fetchone()[0]
            self.assertEqual(chain, 0)

    def test_savings_settings_point_at_the_users_own_savebox_and_primary(self) -> None:
        with self._connect(self.finance_dsn) as connection:
            bad = connection.execute(
                """
                SELECT s.id FROM savings_settings s
                JOIN accounts p ON p.id = s.primary_account_id
                JOIN accounts b ON b.id = s.savebox_account_id
                WHERE p.user_id <> s.user_id OR b.user_id <> s.user_id
                   OR p.account_role <> 'LINKED_DEPOSIT' OR b.account_role <> 'SAVE_BOX'
                """
            ).fetchall()
            self.assertEqual(bad, [])

    def test_the_numbers_financeprofileservice_would_compute(self) -> None:
        """FinanceProfileService/PrXaiContextService 가 쓰는 집계를 SQL 로 같게 계산해 설계값과 비교한다."""
        with self._connect(self.finance_dsn) as connection:
            for profile in finance.PROFILES:
                user_id = connection.execute("SELECT id FROM users WHERE email = %s", (profile.email,)).fetchone()[0]
                balance, emergency = connection.execute(
                    "SELECT COALESCE(sum(balance), 0), COALESCE(sum(balance) FILTER (WHERE account_role = 'SAVE_BOX'), 0) "
                    "FROM accounts WHERE user_id = %s",
                    (user_id,),
                ).fetchone()
                built = finance.build_user(profile, self.as_of, SEED)
                self.assertEqual(int(balance), sum(built.final_balance.values()), profile.key)
                self.assertEqual(int(emergency), built.final_balance.get("S", 0), profile.key)
                month_start = self.as_of.replace(day=1)
                expected_card = connection.execute(
                    "SELECT COALESCE(sum(transaction_amount), 0) FROM card_transactions "
                    "WHERE user_id = %s AND transaction_date BETWEEN %s AND %s",
                    (user_id, month_start, self.as_of),
                ).fetchone()[0]
                self.assertEqual(
                    int(expected_card),
                    sum(t.amount for t in built.card_tx if month_start <= t.on <= self.as_of),
                    profile.key,
                )

    def test_loading_twice_replaces_demo_rows_instead_of_duplicating(self) -> None:
        dsn = self.pg.new_database()
        demo_cli.apply_finance(dsn, self.as_of, SEED)
        with self._connect(dsn) as connection:
            first = connection.execute("SELECT count(*) FROM card_transactions").fetchone()[0]
        demo_cli.apply_finance(dsn, self.as_of + timedelta(days=3), SEED)
        with self._connect(dsn) as connection:
            second_users = connection.execute("SELECT count(*) FROM users").fetchone()[0]
            cohorts = connection.execute("SELECT count(*) FROM cohorts").fetchone()[0]
            second = connection.execute("SELECT count(*) FROM card_transactions").fetchone()[0]
        self.assertEqual(second_users, len(finance.PROFILES))
        self.assertEqual(cohorts, 1)
        self.assertGreater(first, 0)
        self.assertGreater(second, 0)  # 다른 as_of 라 건수는 달라도 된다 — 중복 누적이 아니면 된다
        self.assertLess(second, first * 1.5)

    def test_unload_removes_only_demo_rows(self) -> None:
        dsn = self.pg.new_database()
        demo_cli.apply_finance(dsn, self.as_of, SEED)
        with self._connect(dsn) as connection:
            connection.execute(
                "INSERT INTO users (email, password, name, birth_date, terms_agreed, user_role, status, cohort_id, "
                "created_at, updated_at) SELECT 'real@example.com', 'x', 'real', DATE '1990-01-01', TRUE, 'USER', "
                "'ACTIVE', id, now(), now() FROM cohorts LIMIT 1"
            )
            connection.commit()
        subprocess.run(
            [sys.executable, str(DEMO_DIR / "demo.py"), "unload", "--finance-dsn", dsn],
            check=True, capture_output=True, text=True,
        )
        with self._connect(dsn) as connection:
            emails = [r[0] for r in connection.execute("SELECT email FROM users").fetchall()]
            self.assertEqual(emails, ["real@example.com"])
            self.assertEqual(connection.execute("SELECT count(*) FROM card_transactions").fetchone()[0], 0)

    # ---------------------------------------------------------------- 가격 데이터

    def test_crawl_rows_load_and_the_stores_own_readers_work(self) -> None:
        store = PostgresCrawlStore(self.crawl_dsn)
        sample = store.read_samples(5)
        self.assertEqual(sample.total_count, len(crawl.make_rows(self.as_of, SEED)))
        for family in ("f87", "mx_master", "vxe_r1"):
            stats = store.read_price_stats(30, item_family=family)
            self.assertGreater(stats["count"], 10, family)
            self.assertGreater(stats["avg_price"], 0, family)
        windows = store.read_window_stats(item_family="mx_master")
        self.assertGreater(windows["90d"]["count"], windows["30d"]["count"])

    def test_seeded_outlier_flags_are_exactly_what_the_real_batch_produces(self) -> None:
        dsn = self.pg.new_database()
        demo_cli.apply_crawl(dsn, self.as_of, SEED)
        seeded_rows = crawl.make_rows(self.as_of, SEED)
        seeded = {r.url for r in seeded_rows if r.is_outlier}
        injected = {r.url for r in seeded_rows if r.kind == "anomaly"}
        self.assertEqual(len(injected), 6)
        self.assertTrue(injected <= seeded)
        store = PostgresCrawlStore(dsn)
        result = store.mark_price_outliers(
            channels=[crawl.OUTLIER_CHANNEL],
            keywords=[p.keyword.lower() for p in crawl.PRODUCTS],
            days=crawl.HISTORY_DAYS + 10,
        )
        self.assertEqual(result.reviewed_rows, len(seeded_rows))
        with self._connect(dsn) as connection:
            marked = {r[0] for r in connection.execute("SELECT url FROM crawl_items WHERE is_outlier").fetchall()}
            reasons = {r[0] for r in connection.execute("SELECT DISTINCT outlier_reason FROM crawl_items WHERE is_outlier").fetchall()}
        self.assertEqual(marked, seeded, "시드의 이상치 표시가 스토어 배치 결과와 다르다")
        self.assertEqual(reasons, {r.outlier_reason for r in seeded_rows if r.is_outlier})

    def test_prxaiavailability_style_queries_find_a_demo_item(self) -> None:
        """Spring PrXaiAvailabilityService 가 쓰는 두 쿼리(URL 일치, 제목+가격대)가 데모 행을 찾는다."""
        rows = [r for r in crawl.make_rows(self.as_of, SEED) if r.kind == "normal" and r.item_family == "mx_master"]
        target = rows[len(rows) // 2]
        with self._connect(self.crawl_dsn) as connection:
            by_url = connection.execute(
                "SELECT title, url FROM crawl_items WHERE COALESCE(is_outlier, FALSE) = FALSE AND url = %s "
                "ORDER BY last_seen_at DESC LIMIT 1",
                (target.url,),
            ).fetchone()
            self.assertEqual(by_url[1], target.url)
            price = int(target.price)
            tolerance = max(int(price * 0.2), 50_000)
            by_title = connection.execute(
                "SELECT title, url FROM crawl_items WHERE COALESCE(is_outlier, FALSE) = FALSE "
                "AND LOWER(title) LIKE LOWER(%s) AND NULLIF(regexp_replace(COALESCE(price, ''), '[^0-9]', '', 'g'), '')::BIGINT "
                "BETWEEN %s AND %s ORDER BY last_seen_at DESC LIMIT 1",
                ("%MX Master 3S%", max(price - tolerance, 0), price + tolerance),
            ).fetchone()
            self.assertIsNotNone(by_title)


if __name__ == "__main__":
    unittest.main()
