from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ..models import CrawlResult, HotDeal
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
    def test_normalize_krw_price_rejects_invalid_values(self) -> None:
        self.assertEqual(
            PostgresCrawlStore._normalize_krw_price("1,200,000원"),
            "1200000",
        )
        self.assertEqual(
            PostgresCrawlStore._normalize_krw_price("KRW 77,500"),
            "77500",
        )
        self.assertEqual(
            PostgresCrawlStore._normalize_krw_price("22,031/100개"),
            "22031",
        )
        self.assertEqual(PostgresCrawlStore._normalize_krw_price("$699"), "1048500")
        self.assertEqual(
            PostgresCrawlStore._normalize_krw_price("USD 699"),
            "1048500",
        )
        self.assertEqual(
            PostgresCrawlStore._normalize_krw_price("JPY 12000"),
            "114000",
        )
        self.assertEqual(
            PostgresCrawlStore._normalize_krw_price("CNY 100"),
            "21500",
        )
        self.assertIsNone(PostgresCrawlStore._normalize_krw_price("EUR 100"))
        self.assertIsNone(PostgresCrawlStore._normalize_krw_price("0원"))
        self.assertIsNone(
            PostgresCrawlStore._normalize_krw_price("1,795,054,950원")
        )

    def test_search_title_normalization_builds_token_text(self) -> None:
        self.assertEqual(
            PostgresCrawlStore._normalize_title_for_search(
                "LG gram PRO 360 16T95TP-KD79K OLED"
            ),
            "lg gram pro 360 16t95tp kd79k oled",
        )
        self.assertEqual(
            PostgresCrawlStore._normalize_title_for_search("LG그램17 듀얼업"),
            "lg gram 17 듀얼업",
        )
        self.assertEqual(
            PostgresCrawlStore._normalize_title_for_search("장순필 순댓국 700그램 5팩"),
            "장순필 순댓국 5팩",
        )
        self.assertEqual(
            PostgresCrawlStore._build_search_token_text("gram lg"),
            " gram lg ",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_store_tokens("[쿠팡] 오뚜기3분 쇠고기 간짜장")
            ),
            " 쿠팡 ",
        )
        self.assertEqual(
            PostgresCrawlStore._normalize_title_for_search(
                "[쿠팡] 오뚜기3분 쇠고기 간짜장, 200g, 4개"
            ),
            "오뚜기 3 쇠고기 간짜장 200g 4",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_brand_tokens("LG gram PRO 360")
            ),
            " lg ",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_model_tokens(
                    "LG gram PRO 360 16T95TP-KD79K OLED"
                )
            ),
            " 16t95tp kd79k ",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_series_tokens(
                    "LG gram PRO 360 16T95TP-KD79K OLED"
                )
            ),
            " gram pro ",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_spec_tokens("장순필 순댓국 700그램 5팩")
            ),
            " 5팩 ",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_spec_tokens(
                    "LG그램 15ZD95U-GX5WK 그램케어 포함 2026년형"
                )
            ),
            "",
        )
        self.assertEqual(
            PostgresCrawlStore._normalize_title_for_search(
                "[알리익스프레스] 멤버스 땅콩버터 크리미 1.13kg"
            ),
            "멤버스 땅콩버터 크리미 1.13kg",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_spec_tokens(
                    "[알리익스프레스] 멤버스 땅콩버터 크리미 1.13kg"
                )
            ),
            " 1.13kg ",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_brand_tokens(
                    "[알리익스프레스] Thermalright Peerless Assassin 120 SE V2"
                )
            ),
            " thermalright ",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_series_tokens(
                    "[알리익스프레스] Thermalright Peerless Assassin 120 SE V2"
                )
            ),
            " peerless assassin ",
        )
        self.assertEqual(
            PostgresCrawlStore._build_token_text(
                PostgresCrawlStore._extract_model_tokens(
                    "[알리익스프레스] Thermalright Peerless Assassin 120 SE V2"
                )
            ),
            " 120 se v2 ",
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
            items=[
                HotDeal(
                    title="USD item",
                    url="https://example.com/views/9",
                    price="USD 99",
                )
            ],
        )
        store.save_result(result)

        insert_query = next(
            entry
            for entry in save_cursor.executed
            if "INSERT INTO crawl_items" in entry[0]
        )
        self.assertEqual(insert_query[1][11], "148500")

    def test_save_result_persists_search_fields(self) -> None:
        init_cursor = _FakeCursor()
        save_cursor = _FakeCursor(fetchone_results=[None])
        connector = _ConnectorFactory(
            [_FakeConnection(init_cursor), _FakeConnection(save_cursor)]
        )
        store = PostgresCrawlStore(dsn="postgresql://test", connector=connector)

        result = CrawlResult(
            source="quasarzone",
            fetched_at=datetime.now(timezone.utc),
            items=[
                HotDeal(
                    title="LG gram PRO 360 16T95TP-KD79K OLED",
                    url="https://example.com/views/10",
                    price="2663350",
                )
            ],
        )
        store.save_result(result)

        insert_query = next(
            entry
            for entry in save_cursor.executed
            if "INSERT INTO crawl_items" in entry[0]
        )
        self.assertEqual(insert_query[1][4], "lg gram pro 360 16t95tp kd79k oled")
        self.assertEqual(insert_query[1][5], " lg gram pro 360 16t95tp kd79k oled ")
        self.assertEqual(insert_query[1][6], "")
        self.assertEqual(insert_query[1][7], " lg ")
        self.assertEqual(insert_query[1][8], " 16t95tp kd79k ")
        self.assertEqual(insert_query[1][9], " gram pro ")
        self.assertEqual(insert_query[1][10], "")

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
        self.assertIn(
            "COALESCE(posted_at_ts, fetched_at)", stats_30d_cursor.executed[0][0]
        )
        self.assertIn("AND is_outlier = FALSE", stats_90d_cursor.executed[0][0])
        self.assertIn(
            "numeric_price BETWEEN %s AND %s", stats_90d_cursor.executed[0][0]
        )

    def test_read_window_stats_uses_search_tokens_for_query_groups(self) -> None:
        init_cursor = _FakeCursor()
        stats_30d_cursor = _FakeCursor(
            fetchone_results=[(1, 2500000.0, 2500000.0, 2500000.0)]
        )
        stats_90d_cursor = _FakeCursor(
            fetchone_results=[(2, 2400000.0, 2300000.0, 2500000.0)]
        )
        connector = _ConnectorFactory(
            [
                _FakeConnection(init_cursor),
                _FakeConnection(stats_30d_cursor),
                _FakeConnection(stats_90d_cursor),
            ]
        )
        store = PostgresCrawlStore(dsn="postgresql://test", connector=connector)

        store.read_window_stats(title_keywords=["gram lg", "LG gram"])

        query, params = stats_30d_cursor.executed[0]
        self.assertIn("search_tokens", query)
        self.assertIsNotNone(params)
        self.assertIn("% lg %", params)
        self.assertIn("% gram %", params)

    def test_read_window_stats_accepts_brand_and_model_tokens(self) -> None:
        init_cursor = _FakeCursor()
        stats_30d_cursor = _FakeCursor(
            fetchone_results=[(2, 2049675.0, 1436000.0, 2663350.0)]
        )
        stats_90d_cursor = _FakeCursor(
            fetchone_results=[(2, 2049675.0, 1436000.0, 2663350.0)]
        )
        connector = _ConnectorFactory(
            [
                _FakeConnection(init_cursor),
                _FakeConnection(stats_30d_cursor),
                _FakeConnection(stats_90d_cursor),
            ]
        )
        store = PostgresCrawlStore(dsn="postgresql://test", connector=connector)

        store.read_window_stats(brand_tokens=["lg"], model_tokens=["16t95tp"])

        query, params = stats_30d_cursor.executed[0]
        self.assertIn("brand_tokens", query)
        self.assertIn("model_tokens", query)
        self.assertIsNotNone(params)
        self.assertIn("% lg %", params)
        self.assertIn("% 16t95tp %", params)

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
