"""가격 이력 조회가 동시 요청에서도 조용히 실패하지 않는지 확인한다.

예전에는 요청마다 PostgresCrawlStore 를 새로 만들었고, 만들 때마다 스키마 점검(ALTER TABLE ... IF NOT EXISTS
등)을 했다. 동시 요청이 서로 교착(DeadlockDetected)해서 조회가 실패하면 서비스는 예외를 삼키고
'NO_PRICE_HISTORY'(요청 가격을 평균가로 대신 사용)로 떨어졌다. 그 결과 같은 입력의 판단이 흔들렸다.

  1) 스토어 쪽: 스키마 점검을 advisory lock 으로 한 번에 하나씩 하게 한다 (프로세스가 여러 개여도 안전).
  2) 서비스 쪽: 스토어를 DSN 당 프로세스에 한 번만 만든다 (요청마다 ALTER TABLE 을 하지 않는다).
"""

from __future__ import annotations

import concurrent.futures as cf
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from domain.xai_purchase import service as xai_service  # noqa: E402

from ..storage.postgres_store import PostgresCrawlStore  # noqa: E402

try:
    from ._pg_fixture import TempPostgres, require_postgres
except ModuleNotFoundError:  # pragma: no cover
    TempPostgres = None  # type: ignore[assignment]


@unittest.skipIf(TempPostgres is None, "_pg_fixture 가 없다")
class StoreInitConcurrencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_postgres()  # 서버 바이너리가 없으면 건너뜀
        cls.pg = TempPostgres()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pg.close()

    def _hammer(self, dsn: str, workers: int = 16, rounds: int = 48) -> list[str]:
        def one(_: int) -> str:
            try:
                store = PostgresCrawlStore(dsn)
                store.read_window_stats(item_family="mx_master")
                return "ok"
            except Exception as exc:  # noqa: BLE001 - 어떤 실패든 센다
                return f"{type(exc).__name__}: {str(exc).splitlines()[0][:100]}"

        with cf.ThreadPoolExecutor(workers) as pool:
            return list(pool.map(one, range(rounds)))

    def test_many_stores_can_initialize_at_once_on_an_empty_database(self) -> None:
        results = self._hammer(self.pg.new_database())
        self.assertEqual(set(results), {"ok"}, f"동시 초기화가 실패했다: {sorted(set(results))}")

    def test_many_stores_can_initialize_at_once_on_an_existing_table_with_rows(self) -> None:
        dsn = self.pg.new_database()
        PostgresCrawlStore(dsn)
        import psycopg

        with psycopg.connect(dsn) as connection:
            connection.execute(
                "INSERT INTO crawl_items (source, post_id, url, title, price, fetched_at, first_seen_at, last_seen_at) "
                "SELECT 's', i::text, 'https://x.invalid/views/' || i, 'MX Master 3S ' || i, '100000', now(), now(), now() "
                "FROM generate_series(1, 300) AS i"
            )
        results = self._hammer(dsn)
        self.assertEqual(set(results), {"ok"}, f"동시 초기화가 실패했다: {sorted(set(results))}")


class ServiceStoreCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        xai_service._reset_crawl_stores()
        self.addCleanup(xai_service._reset_crawl_stores)

    def test_store_is_created_once_per_dsn_even_under_threads(self) -> None:
        created: list[str] = []
        gate = threading.Barrier(12)

        class FakeStore:
            def __init__(self, dsn: str) -> None:
                created.append(dsn)

        with patch.object(xai_service, "PostgresCrawlStore", FakeStore):
            def grab(_: int):
                gate.wait()
                return xai_service._crawl_store("postgresql://a")

            with cf.ThreadPoolExecutor(12) as pool:
                stores = list(pool.map(grab, range(12)))
            other = xai_service._crawl_store("postgresql://b")

        self.assertEqual(created, ["postgresql://a", "postgresql://b"])
        self.assertTrue(all(store is stores[0] for store in stores))
        self.assertIsNot(other, stores[0])

    def test_failed_initialization_is_not_cached(self) -> None:
        attempts = {"n": 0}

        class FlakyStore:
            def __init__(self, dsn: str) -> None:
                attempts["n"] += 1
                if attempts["n"] == 1:
                    raise RuntimeError("db down")

        with patch.object(xai_service, "PostgresCrawlStore", FlakyStore):
            with self.assertRaises(RuntimeError):
                xai_service._crawl_store("postgresql://a")
            store = xai_service._crawl_store("postgresql://a")  # DB 가 돌아오면 다음 요청이 다시 시도한다
            self.assertIs(store, xai_service._crawl_store("postgresql://a"))
        self.assertEqual(attempts["n"], 2)

    def test_read_window_stats_reports_failure_instead_of_hiding_it(self) -> None:
        class DownStore(PostgresCrawlStore):  # classify_item_family 등 정적 메서드는 그대로 쓴다
            def __init__(self, dsn: str) -> None:
                raise RuntimeError("db down")

        with patch.object(xai_service, "PostgresCrawlStore", DownStore), patch(
            "config.get_env", side_effect=lambda name, default=None: "postgresql://a" if name == "AI_POSTGRES_DSN" else default
        ):
            stats, warnings = xai_service._read_window_stats(130_000, "MX Master 3S", None)
        self.assertIn("PRICE_HISTORY_READ_FAILED", warnings)
        self.assertIn("NO_PRICE_HISTORY", warnings)
        self.assertEqual(stats["30d"]["avg_price"], 130_000.0)


if __name__ == "__main__":
    unittest.main()
