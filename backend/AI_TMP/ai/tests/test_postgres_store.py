from __future__ import annotations

from datetime import datetime
from datetime import timezone
import unittest

from ..models import CrawlResult
from ..models import HotDeal
from ..storage.postgres_store import PostgresCrawlStore


class _FakeCursor:
    def __init__(
        self,
        fetchone_results: list[object | None] | None = None,
        fetchall_results: list[tuple[object, ...]] | None = None,
    ) -> None:
        self.executed: list[tuple[str, tuple[object, ...] | None]] = []
        self._fetchone_results = list(fetchone_results or [])
        self._fetchall_results = list(fetchall_results or [])

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        self.executed.append((query, params))

    def fetchone(self) -> object | None:
        if not self._fetchone_results:
            return None
        return self._fetchone_results.pop(0)

    def fetchall(self) -> list[tuple[object, ...]]:
        return list(self._fetchall_results)

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        return False


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor

    def cursor(self) -> _FakeCursor:
        return self._cursor

    def __enter__(self) -> _FakeConnection:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        return False


class _ConnectorFactory:
    def __init__(self, connections: list[_FakeConnection]) -> None:
        self._connections = list(connections)

    def __call__(self, dsn: str) -> _FakeConnection:
        self.last_dsn = dsn
        return self._connections.pop(0)


class PostgresCrawlStoreTest(unittest.TestCase):
    def test_normalize_krw_price_rejects_foreign_currency(self) -> None:
        self.assertEqual(PostgresCrawlStore._normalize_krw_price("1,200,000원"), "1200000")
        self.assertEqual(PostgresCrawlStore._normalize_krw_price("₩899,000"), "899000")
        self.assertEqual(PostgresCrawlStore._normalize_krw_price("KRW 77,500"), "77500")
        self.assertEqual(PostgresCrawlStore._normalize_krw_price("$699"), "1048500")
        self.assertEqual(PostgresCrawlStore._normalize_krw_price("USD 699"), "1048500")
        self.assertEqual(PostgresCrawlStore._normalize_krw_price("JPY 12000"), "114000")
        self.assertEqual(PostgresCrawlStore._normalize_krw_price("¥12000"), "114000")
        self.assertEqual(PostgresCrawlStore._normalize_krw_price("CNY 100"), "21500")
        self.assertIsNone(PostgresCrawlStore._normalize_krw_price("EUR 100"))

    def test_classify_item_family_maps_supported_three_products(self) -> None:
        self.assertEqual(
            PostgresCrawlStore.classify_item_family(title="F87 pro \ud0a4\ubcf4\ub4dc", url=None),
            "f87",
        )
        self.assertEqual(
            PostgresCrawlStore.classify_item_family(title="\ub3c5\uac70\ubbf8 87", url=None),
            "f87",
        )
        self.assertEqual(
            PostgresCrawlStore.classify_item_family(title="mx master 3s", url=None),
            "mx_master",
        )
        self.assertEqual(
            PostgresCrawlStore.classify_item_family(title="mx \ub9c8\uc2a4\ud130 3", url=None),
            "mx_master",
        )
        self.assertEqual(
            PostgresCrawlStore.classify_item_family(title="VXE R1 mouse", url=None),
            "vxe_r1",
        )

    def test_save_result_counts_inserted_and_updated(self) -> None:
        init_cursor = _FakeCursor()
        save_cursor = _FakeCursor(fetchone_results=[None, (1,)])
        connector = _ConnectorFactory(
            [_FakeConnection(init_cursor), _FakeConnection(save_cursor)]
        )
        store = PostgresCrawlStore(dsn="postgresql://test", connector=connector)

        result = CrawlResult(
            source="quasarzone",
            fetched_at=datetime.now(timezone.utc),
            items=[
                HotDeal(title="New", url="https://example.com/views/1", price="1000"),
                HotDeal(title="Old", url="https://example.com/views/2", price="2000"),
            ],
        )
        stats = store.save_result(result)

        self.assertEqual(stats.inserted, 1)
        self.assertEqual(stats.updated, 1)
        self.assertGreaterEqual(len(save_cursor.executed), 4)

    def test_save_result_converts_foreign_currency_to_krw(self) -> None:
        init_cursor = _FakeCursor()
        save_cursor = _FakeCursor(fetchone_results=[None])
        connector = _ConnectorFactory(
            [_FakeConnection(init_cursor), _FakeConnection(save_cursor)]
        )
        store = PostgresCrawlStore(dsn="postgresql://test", connector=connector)

        result = CrawlResult(
            source="quasarzone",
            fetched_at=datetime.now(timezone.utc),
            items=[HotDeal(title="USD item", url="https://example.com/views/9", price="USD 99")],
        )
        store.save_result(result)

        insert_query = next(
            entry for entry in save_cursor.executed if "INSERT INTO crawl_items" in entry[0]
        )
        self.assertEqual(insert_query[1][4], "148500")

    def test_is_seen_returns_true_when_row_exists(self) -> None:
        init_cursor = _FakeCursor()
        check_cursor = _FakeCursor(fetchone_results=[(1,)])
        connector = _ConnectorFactory(
            [_FakeConnection(init_cursor), _FakeConnection(check_cursor)]
        )
        store = PostgresCrawlStore(dsn="postgresql://test", connector=connector)

        seen = store.is_seen(
            HotDeal(title="Deal", url="https://example.com/views/7", price="1000")
        )

        self.assertTrue(seen)

    def test_read_samples_returns_expected_payload(self) -> None:
        init_cursor = _FakeCursor()
        sample_cursor = _FakeCursor(
            fetchone_results=[(2,)],
            fetchall_results=[
                ("10", "A", "1000", "https://example.com/10"),
                ("9", "B", None, "https://example.com/9"),
            ],
        )
        connector = _ConnectorFactory(
            [_FakeConnection(init_cursor), _FakeConnection(sample_cursor)]
        )
        store = PostgresCrawlStore(dsn="postgresql://test", connector=connector)

        sample_result = store.read_samples(sample_limit=2)

        self.assertEqual(sample_result.total_count, 2)
        self.assertEqual(len(sample_result.sample_items), 2)
        self.assertEqual(sample_result.sample_items[0]["post_id"], "10")
        self.assertEqual(sample_result.sample_items[1]["price"], None)

    def test_read_window_stats_returns_30d_and_90d(self) -> None:
        init_cursor = _FakeCursor()
        stats_30d_cursor = _FakeCursor(fetchone_results=[(3, 1200.0, 1000.0, 1500.0)])
        stats_90d_cursor = _FakeCursor(fetchone_results=[(8, 1400.0, 900.0, 2000.0)])
        connector = _ConnectorFactory(
            [
                _FakeConnection(init_cursor),
                _FakeConnection(stats_30d_cursor),
                _FakeConnection(stats_90d_cursor),
            ]
        )
        store = PostgresCrawlStore(dsn="postgresql://test", connector=connector)

        stats = store.read_window_stats(item_family="f87 pro")

        self.assertEqual(stats["30d"]["count"], 3)
        self.assertEqual(stats["30d"]["avg_price"], 1200.0)
        self.assertEqual(stats["90d"]["max_price"], 2000.0)

        self.assertIn(
            "COALESCE(posted_at_ts, fetched_at)", stats_30d_cursor.executed[0][0]
        )
        self.assertIn(
            "AND is_outlier = FALSE", stats_90d_cursor.executed[0][0]
        )
        self.assertIn("item_family = %s", stats_30d_cursor.executed[0][0])
        self.assertEqual(stats_30d_cursor.executed[0][1], (30, "f87"))

    def test_mark_price_outliers_marks_only_out_of_iqr_range(self) -> None:
        init_cursor = _FakeCursor()
        mark_cursor = _FakeCursor(
            fetchall_results=[
                ("https://example.com/views/1", "F87 pro A", 100000),
                ("https://example.com/views/2", "F87 pro B", 103000),
                ("https://example.com/views/3", "F87 pro C", 106000),
                ("https://example.com/views/4", "F87 pro D", 110000),
                ("https://example.com/views/5", "F87 pro E", 2000000),
            ]
        )
        connector = _ConnectorFactory(
            [_FakeConnection(init_cursor), _FakeConnection(mark_cursor)]
        )
        store = PostgresCrawlStore(dsn="postgresql://test", connector=connector)

        result = store.mark_price_outliers(
            channels=["quasarzone"],
            keywords=["F87 pro"],
            days=90,
            iqr_multiplier=1.5,
            min_group_size=4,
        )

        self.assertEqual(result.reviewed_rows, 5)
        self.assertEqual(result.marked_rows, 1)
        self.assertEqual(len(result.scopes), 1)
        self.assertEqual(result.scopes[0].channel, "quasarzone")
        self.assertEqual(result.scopes[0].keyword, "f87 pro")
        self.assertEqual(result.scopes[0].marked_count, 1)

        update_queries = [
            entry for entry in mark_cursor.executed if "UPDATE crawl_items" in entry[0]
        ]
        self.assertGreaterEqual(len(update_queries), 2)
        self.assertIn("is_outlier = TRUE", update_queries[-1][0])


if __name__ == "__main__":
    unittest.main()
