"""DB 에서 제목을 뽑고 사람이 붙인 정답을 읽는 도구 테스트 (가짜 연결 사용).

실제 크롤 테이블은 crawl_items(source, post_id, url, title, price, posted_at, fetched_at,
first_seen_at, last_seen_at) 이다. 이 도구는 읽기 전용이다.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from ..crawler.identity.dbio import default_dsn, fetch_labels, fetch_titles
from ..scripts.eval_product_identity import load_labeled
from ..scripts.export_unresolved_titles import build_template


class FakeCursor:
    def __init__(self, rows, log):
        self.rows, self.log = rows, log

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.log.append((" ".join(sql.split()), params))

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self.rows, self.log, self.closed = rows, [], False

    def cursor(self):
        return FakeCursor(self.rows, self.log)

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False


def connector(rows):
    holder = {}

    def connect(dsn):
        holder["conn"] = FakeConnection(rows)
        holder["dsn"] = dsn
        return holder["conn"]

    return connect, holder


class FetchTitlesTest(unittest.TestCase):
    def test_제목만_읽고_빈_제목은_버린다(self) -> None:
        connect, holder = connector([("로지텍 G304",), ("",), (None,), ("  ",), ("키크론 K8",)])

        titles = fetch_titles("dsn", connector=connect)

        self.assertEqual(titles, ["로지텍 G304", "키크론 K8"])
        self.assertTrue(holder["conn"].closed)

    def test_출처와_기간과_개수_조건을_매개변수로_넘긴다(self) -> None:
        connect, holder = connector([])

        fetch_titles("dsn", source="quasarzone", since="2025-01-01", limit=500, connector=connect)

        sql, params = holder["conn"].log[0]
        self.assertIn("FROM crawl_items", sql)
        self.assertIn("source = %s", sql)
        self.assertIn("last_seen_at >= %s", sql)
        self.assertIn("LIMIT %s", sql)
        self.assertEqual(list(params), ["quasarzone", "2025-01-01", 500])
        self.assertNotIn("quasarzone", sql)  # 값은 SQL 에 끼워 넣지 않고 매개변수로만 넘긴다

    def test_조건이_없으면_전체를_최근순으로(self) -> None:
        connect, holder = connector([])

        fetch_titles("dsn", connector=connect)

        sql, params = holder["conn"].log[0]
        self.assertNotIn("WHERE", sql)
        self.assertIn("ORDER BY last_seen_at DESC", sql)
        self.assertEqual(list(params or []), [])


class FetchLabelsTest(unittest.TestCase):
    def test_title과_id_열의_정답을_평가_형식으로_바꾼다(self) -> None:
        connect, _ = connector([("로지텍 MX Master 3S", "logitech:mx-master-3s"), ("오늘의 핫딜", None), ("로지텍 G304", "")])

        rows = fetch_labels("dsn", "SELECT title, product_id FROM labeled_titles", connector=connect)

        self.assertEqual(rows, [
            {"kind": "labeled", "title": "로지텍 MX Master 3S", "id": "logitech:mx-master-3s"},
            {"kind": "labeled", "title": "오늘의 핫딜", "id": None},
            {"kind": "labeled", "title": "로지텍 G304", "id": None},
        ])

    def test_SELECT_하나만_허용한다(self) -> None:
        connect, holder = connector([])
        for bad in ("DELETE FROM crawl_items", "SELECT 1; DROP TABLE x", "UPDATE t SET a=1", "  insert into t values (1)", "", "WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x"):
            with self.subTest(sql=bad):
                with self.assertRaises(ValueError):
                    fetch_labels("dsn", bad, connector=connect)
        self.assertNotIn("conn", holder)  # 연결조차 열지 않았다

    def test_주석으로_가장한_다중_문장도_막는다(self) -> None:
        connect, _ = connector([])

        with self.assertRaises(ValueError):
            fetch_labels("dsn", "SELECT title, id FROM t -- x\n; DROP TABLE t", connector=connect)


class DefaultDsnTest(unittest.TestCase):
    def test_AI_POSTGRES_DSN이_우선한다(self) -> None:
        from unittest.mock import patch

        with patch.dict("os.environ", {"AI_POSTGRES_DSN": "postgresql://u:p@h:1/d"}):
            self.assertEqual(default_dsn(), "postgresql://u:p@h:1/d")

    def test_조각_환경변수로_조립한다(self) -> None:
        from unittest.mock import patch

        env = {"AI_POSTGRES_DSN": "", "AI_POSTGRES_HOST": "db", "AI_POSTGRES_PORT": "5433", "AI_POSTGRES_DB": "x",
               "AI_POSTGRES_USER": "me", "AI_POSTGRES_PASSWORD": "pw"}
        with patch.dict("os.environ", env):
            self.assertEqual(default_dsn(), "postgresql://me:pw@db:5433/x")


class LabelFileTest(unittest.TestCase):
    def test_CSV_정답_파일을_읽는다(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["title", "id", "kind", "note"])
                writer.writerow(["로지텍 MX Master 3S", "logitech:mx-master-3s", "labeled", ""])
                writer.writerow(["오늘의 핫딜", "", "labeled", "상품 아님"])

            rows = load_labeled(path)

        self.assertEqual(rows[0]["id"], "logitech:mx-master-3s")
        self.assertIsNone(rows[1]["id"])
        self.assertEqual(rows[1]["note"], "상품 아님")

    def test_JSON_정답_파일을_읽는다(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.json"
            path.write_text(json.dumps({"rows": [{"title": "a", "id": None}]}), encoding="utf-8")

            self.assertEqual(load_labeled(path), [{"title": "a", "id": None}])

    def test_라벨링_템플릿의_제목에_정답을_채우면_그대로_평가할_수_있다(self) -> None:
        template = build_template(["로지텍 M590 무선 마우스", "로지텍 MX Master 마우스"])
        for row in template["rows"]:
            row["id"] = None  # 사람이 '카탈로그에 없음'으로 표시

        from ..scripts.eval_product_identity import evaluate

        result = evaluate(template["rows"])

        self.assertEqual(result["false_merge"], 0)
        self.assertEqual(result["counts"]["correct_refusal"], 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
