"""상품 식별 평가: 오병합(서로 다른 상품을 같은 상품으로 합침)을 센다.

    cd backend/AI_TMP
    python -m ai.scripts.eval_product_identity
    python -m ai.scripts.eval_product_identity --labeled path/to/real_labeled.json   # JSON 또는 CSV
    python -m ai.scripts.eval_product_identity --labels-sql "SELECT title, product_id FROM labeled_titles"

읽는 법 (중요)
    기본으로 쓰는 평가 세트는 합성이다 (tests/fixtures/crawler/identity_labeled.json). 제목도
    카탈로그도 같은 사람이 만들었으므로 '재현율'은 낙관적이다. 이 평가가 의미 있게 확인하는 것은
    설계 성질 하나다: 신뢰 식별(trusted)이 나온 건 중 틀린 건(오병합)이 0 인가.
    실제 서버에서 수집한 제목에 사람이 정답을 붙인 세트가 생기면 --labeled 로 같은 지표를 잰다.

지표
    false_merge : 신뢰 식별을 냈는데 정답 id 와 다름 (정답이 null 이면 신뢰 식별 자체가 오류)
    correct     : 신뢰 식별이 정답 id 와 같음
    missed      : 정답 id 가 있는데 신뢰 식별을 내지 못함 (정밀도를 위해 포기한 것)
    precision   : correct / (correct + false_merge)
    recall      : correct / (correct + missed)
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import sys
from typing import Any, Iterable

ROOT_PARENT = Path(__file__).resolve().parents[2]
if str(ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(ROOT_PARENT))

from ai.crawler.identity import ProductResolver  # noqa: E402

DEFAULT_LABELED = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "crawler" / "identity_labeled.json"


def load_labeled(path: Path) -> list[dict[str, Any]]:
    """정답 파일(JSON {"rows": [...]} 또는 CSV[title,id,kind,note])을 읽는다. 빈 id 는 None."""
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return [
                {"kind": row.get("kind") or "labeled", "title": row["title"], "id": (row.get("id") or "").strip() or None,
                 **({"note": row["note"]} if row.get("note") else {})}
                for row in csv.DictReader(handle)
                if row.get("title")
            ]
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def evaluate(rows: Iterable[dict[str, Any]], resolver: ProductResolver | None = None) -> dict[str, Any]:
    resolver = resolver or ProductResolver()
    totals: Counter[str] = Counter()
    by_kind: dict[str, Counter[str]] = defaultdict(Counter)
    false_merges: list[dict[str, Any]] = []
    missed: list[dict[str, Any]] = []
    statuses: Counter[str] = Counter()

    for row in rows:
        identity = resolver.resolve(row["title"])
        gold = row.get("id")
        statuses[identity.status.value] += 1
        if identity.trusted:
            outcome = "correct" if identity.canonical_id == gold else "false_merge"
        else:
            outcome = "missed" if gold is not None else "correct_refusal"
        totals[outcome] += 1
        by_kind[row.get("kind", "unknown")][outcome] += 1
        record = {"title": row["title"], "gold": gold, "got": identity.canonical_id, "status": identity.status.value}
        if outcome == "false_merge":
            false_merges.append(record)
        elif outcome == "missed":
            missed.append({**record, "note": row.get("note", "")})

    correct, fm, miss = totals["correct"], totals["false_merge"], totals["missed"]
    return {
        "rows": sum(totals.values()),
        "counts": dict(totals),
        "precision": (correct / (correct + fm)) if (correct + fm) else None,
        "recall": (correct / (correct + miss)) if (correct + miss) else None,
        "false_merge": fm,
        "by_kind": {k: dict(v) for k, v in by_kind.items()},
        "status_counts": dict(statuses),
        "false_merges": false_merges,
        "missed": missed,
    }


def summarize(result: dict[str, Any], *, synthetic: bool) -> str:
    lines = [
        "상품 식별 평가",
        f"  제목 {result['rows']}개",
        f"  정답으로 확정 {result['counts'].get('correct', 0)} / 오병합 {result['false_merge']} / 놓침 {result['counts'].get('missed', 0)} / 올바르게 거부 {result['counts'].get('correct_refusal', 0)}",
        f"  정밀도 {result['precision']:.3f}" if result["precision"] is not None else "  정밀도 -",
        f"  재현율 {result['recall']:.3f}" if result["recall"] is not None else "  재현율 -",
        "  종류별: " + ", ".join(f"{k} {dict(v)}" for k, v in result["by_kind"].items()),
        "  판정 상태: " + ", ".join(f"{k} {v}" for k, v in sorted(result["status_counts"].items())),
    ]
    for item in result["false_merges"]:
        lines.append(f"  !! 오병합: {item['title']!r} -> {item['got']} (정답 {item['gold']})")
    for item in result["missed"]:
        lines.append(f"  놓침: {item['title']!r} (정답 {item['gold']}, 판정 {item['status']}) {item['note']}")
    if synthetic:
        lines += ["", "주의: 평가 세트와 카탈로그가 같은 사람이 만든 합성이라 재현율은 낙관적이다.",
                  "      확인하는 것은 '오병합 0' 이라는 설계 성질이다. 실제 제목에 정답을 붙인 세트로 다시 재야 한다."]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate product identity resolution")
    parser.add_argument("--labeled", type=Path, default=DEFAULT_LABELED, help="정답 파일(JSON 또는 CSV)")
    parser.add_argument("--labels-sql", help="DB 에서 정답을 읽는 SELECT (title, id 두 열). --dsn 또는 AI_POSTGRES_* 사용")
    parser.add_argument("--dsn")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.labels_sql:
        from ai.crawler.identity.dbio import default_dsn, fetch_labels

        rows = fetch_labels(args.dsn or default_dsn(), args.labels_sql)
        synthetic = False
    else:
        rows = load_labeled(args.labeled)
        synthetic = args.labeled == DEFAULT_LABELED
    result = evaluate(rows)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else summarize(result, synthetic=synthetic))


if __name__ == "__main__":
    main()
