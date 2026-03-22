from __future__ import annotations

from datetime import datetime
from datetime import timezone
import unittest

from ai.models import CrawlResult
from ai.models import HotDeal
from ai.storage.postgres_store import PostgresCrawlStore


class _FakeCursor:
    def __init__(
        self,
        fetchone_results: list[object | None] | None = None,
        fetchall_results: list[tuple[str | None, str, str | None, str]] | None = None,
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

    def fetchall(self) -> list[tuple[str | None, str, str | None, str]]:
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

        stats = store.read_window_stats()

        self.assertEqual(stats["30d"]["count"], 3)
        self.assertEqual(stats["30d"]["avg_price"], 1200.0)
        self.assertEqual(stats["90d"]["max_price"], 2000.0)


if __name__ == "__main__":
    unittest.main()
