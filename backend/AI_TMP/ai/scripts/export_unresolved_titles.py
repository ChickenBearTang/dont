"""사람이 정답을 붙일 제목을 뽑는다 (실제 정답 세트를 만들기 위한 첫 단계).

    cd backend/AI_TMP
    python -m ai.scripts.export_unresolved_titles --input crawled_titles.jsonl --output to_label.json

입력: 한 줄에 하나인 JSON({"title": ...}) 또는 'title' 열이 있는 CSV.
출력: 신뢰 식별이 나오지 않은 제목만 담은 라벨링 템플릿. 사람이 각 행의 "id" 에 카탈로그
상품 ID 를 넣거나(카탈로그에 없으면 null 로 두고 note 에 이유) 카탈로그에 상품을 추가한다.
완성한 파일은 `ai.scripts.eval_product_identity --labeled` 로 바로 평가할 수 있다.
같은 정규화 제목은 한 번만, 많이 나온 것부터 낸다 (라벨링 노력 대비 효과가 큰 순서).
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Iterable

ROOT_PARENT = Path(__file__).resolve().parents[2]
if str(ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(ROOT_PARENT))

from ai.crawler.identity import ProductResolver  # noqa: E402
from ai.crawler.identity.text import tokenize  # noqa: E402


def read_titles(path: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            return [row["title"] for row in csv.DictReader(handle) if row.get("title")]
    titles: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            title = json.loads(line).get("title")
            if isinstance(title, str) and title.strip():
                titles.append(title)
    return titles


def build_template(titles: Iterable[str], resolver: ProductResolver | None = None) -> dict[str, Any]:
    resolver = resolver or ProductResolver()
    counts: Counter[str] = Counter()
    sample: dict[str, str] = {}
    for title in titles:
        key = " ".join(tokenize(title))
        counts[key] += 1
        sample.setdefault(key, title)

    rows: list[dict[str, Any]] = []
    trusted = 0
    for key, count in counts.most_common():
        identity = resolver.resolve(sample[key])
        if identity.trusted:
            trusted += 1
            continue
        rows.append({
            "kind": "unlabeled", "title": sample[key], "id": None, "seen": count,
            "resolver_status": identity.status.value, "resolver_candidates": list(identity.candidates),
            "resolver_guess": identity.model, "note": "",
        })
    return {
        "_comment": "라벨링 템플릿. id 에 카탈로그 상품 ID 를 넣거나, 해당 상품이 없으면 null 로 두고 note 에 이유를 적는다.",
        "summary": {"unique_titles": len(counts), "trusted": trusted, "to_label": len(rows)},
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export titles that need human labels")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    template = build_template(read_titles(args.input))
    args.output.write_text(json.dumps(template, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(template["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
