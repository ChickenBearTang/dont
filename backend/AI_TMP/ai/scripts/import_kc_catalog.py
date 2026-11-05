"""공공 인증 DB(KC/전파 적합성평가) 내려받은 파일로 카탈로그를 만든다.

    cd backend/AI_TMP
    python -m ai.scripts.import_kc_catalog \\
        --input rra_self_conformity.csv [--input more.json ...] \\
        --curated ai/crawler/identity/data/catalog_seed.json \\
        --aliases kc_aliases.csv \\
        --output ai/crawler/identity/data/catalog_kc.json \\
        --report kc_import_report.json

    # 쓰려면 (시드 다음에 읽힌다)
    export AI_PRODUCT_CATALOG_PATHS=ai/crawler/identity/data/catalog_kc.json

입력은 공공데이터포털에서 받아 둔 CSV/JSON/XML 이다. 온프레미스 원칙상 런타임에 API 를 부르지 않는다.
--aliases 는 (catalog_id, alias) CSV 로, 검수한 카탈로그 상품(마케팅 이름)과 인증 모델 코드를 잇는다.
보고서의 unmapped_manufacturers 는 brands.json 에 추가할 제조자 목록이고, conflicts 와
dropped_aliases 는 사람이 확인할 충돌이다.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT_PARENT = Path(__file__).resolve().parents[2]
if str(ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(ROOT_PARENT))

from ai.crawler.identity.brands import BrandLexicon  # noqa: E402
from ai.crawler.identity.kc_import import (  # noqa: E402
    build_entries,
    merge_with_curated,
    read_kc_records,
    write_catalog,
)


def run(
    inputs: list[Path],
    *,
    curated_path: Path | None = None,
    aliases_path: Path | None = None,
    mapping: dict[str, list[str]] | None = None,
    lexicon: BrandLexicon | None = None,
) -> tuple[list[dict], dict]:
    lexicon = lexicon or BrandLexicon.load()
    records: list[dict] = []
    reads = []
    for path in inputs:
        part, info = read_kc_records(path, mapping=mapping)
        records += part
        reads.append({"file": str(path), **info})
    built = build_entries(records, lexicon)
    report = {"inputs": reads, **built.report}

    entries = built.entries
    if curated_path is not None:
        curated = [dict(p) for p in json.loads(curated_path.read_text(encoding="utf-8"))["products"]]
        alias_rows: list[tuple[str, str]] = []
        if aliases_path is not None:
            with aliases_path.open(encoding="utf-8-sig", newline="") as handle:
                alias_rows = [(r["catalog_id"].strip(), r["alias"].strip()) for r in csv.DictReader(handle) if r.get("alias")]
        merged = merge_with_curated(entries, curated, alias_rows)
        entries = [e for e in merged.entries if e.get("source") == "kc" or e["id"] in {c["id"] for c in curated}]
        # 출력 파일에는 KC 에서 온 항목과, KC 정보를 흡수한 검수 항목만 담는다 (시드 전체를 복사하지 않는다).
        absorbed_into = {m["into"] for m in merged.report["absorbed"]}
        entries = [e for e in entries if e.get("source") == "kc" or e["id"] in absorbed_into or (aliases_path and e["id"] in {a[0] for a in alias_rows})]
        report.update(merge=merged.report)
    report["output_entries"] = len(entries)
    return entries, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a catalog from public certification data")
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--curated", type=Path)
    parser.add_argument("--aliases", type=Path)
    parser.add_argument("--mapping", type=Path, help='열 이름 매핑 JSON, 예: {"model": ["모델"]}')
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    mapping = json.loads(args.mapping.read_text(encoding="utf-8")) if args.mapping else None
    entries, report = run(args.input, curated_path=args.curated, aliases_path=args.aliases, mapping=mapping)
    write_catalog(args.output, entries)
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("records", "entries", "output_entries") if k in report}, ensure_ascii=False))
    print(f"제조자 사전에 없는 곳 {len(report.get('unmapped_manufacturers', {}))}곳, 충돌 {len(report.get('conflicts', []))}건")


if __name__ == "__main__":
    main()
