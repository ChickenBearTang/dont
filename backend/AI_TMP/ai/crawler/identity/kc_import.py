"""공공 인증 DB(KC/전파 적합성평가)에서 카탈로그를 만든다.

왜 인증 DB 인가
    한국에 정식으로 들어온 전자기기는 인증을 받고, 그 기록(제조자, 모델 코드, 관리번호)이 공개된다.
    직접 쓴 카탈로그보다 '실제로 존재하는 제조자-모델 조합'의 근거가 훨씬 단단하다.

이 DB 가 주지 못하는 것 (설계에 반영한 한계)
    1. 마케팅 이름이 없다. 인증 기록은 'SM-R510' 같은 규제용 모델 코드와 일반 명칭(예: 무선이어폰)을
       담는다. 제목에 쓰는 '갤럭시 버즈2 프로' 와의 연결은 별칭 파일(catalog_id,alias)로 사람이
       이어 줘야 한다 (merge_with_curated).
    2. 인증 대상이 아닌 상품은 없다 (식품, 생활용품, 직구/병행수입 등). 핫딜 글의 상당수가 해당한다.
    3. 인증 한 건이 상품 한 개가 아니다. 같은 상품이 여러 번(색상/지역 SKU, 재인증) 인증된다.
       그래서 기본모델 기준으로 합치고 파생모델은 별칭으로 삼는다.
    4. 제조자 표기가 법인명이다 ('삼성전자(주)', 'Logitech Europe S.A.'). 브랜드 사전으로 바꾸고,
       사전에 없는 제조자는 보고서로 알려 준다 (brands.json 에 추가하면 된다).

열 이름은 국립전파연구원 '자기적합확인 DB정보' OpenAPI 의 응답 항목(업체명, 기자재명칭, 기본모델,
파생모델, 관리번호, 제조자, 제조국가, 공개년월일)을 기준으로 했다. 실제 응답 스키마는 활용가이드로
확인해야 하며, 다르면 mapping 으로 바꾼다. 온프레미스 원칙상 API 를 런타임에 부르지 않고, 받아 둔
파일(CSV/JSON/XML)을 이 모듈로 한 번 변환해 카탈로그 JSON 으로 쓴다.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import csv
import io
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping
import xml.etree.ElementTree as ET

from .brands import BrandLexicon
from .text import compact_code

DEFAULT_MAPPING: dict[str, list[str]] = {
    "model": ["기본모델", "기본모델명", "모델명", "model", "basicmodel", "basic_model"],
    "derived": ["파생모델", "파생모델명", "derivedmodel", "derived_model"],
    "manufacturer": ["제조자", "제조업체", "제조사", "manufacturer", "maker"],
    "company": ["업체명", "신청인", "상호", "company", "applicant"],
    "equipment": ["기자재명칭", "기자재명", "품목", "품명", "itemname", "equipment"],
    "management_no": ["관리번호", "인증번호", "certno", "certnum", "mngno", "management_no"],
    "date": ["공개년월일", "인증일자", "certdate", "date"],
    "country": ["제조국가", "제조국", "country"],
}

MIN_CODE_LEN = 2
_SPLIT = re.compile(r"[,;/|\n]+")
_MAX_XML_BYTES = 200 * 1024 * 1024


def _norm_key(key: str) -> str:
    return re.sub(r"[\s_\-]", "", str(key)).lower()


def _pick(row: Mapping[str, Any], candidates: Iterable[str]) -> Any:
    index = {_norm_key(k): v for k, v in row.items()}
    for name in candidates:
        value = index.get(_norm_key(name))
        if value not in (None, ""):
            return value
    return None


def _flatten_items(node: Any) -> list[dict[str, Any]]:
    """data.go.kr 응답에서 항목 목록을 찾는다 (response.body.items.item 등 여러 모양)."""
    if isinstance(node, list):
        if node and all(isinstance(x, dict) for x in node):
            return node
        out: list[dict[str, Any]] = []
        for x in node:
            out += _flatten_items(x)
        return out
    if isinstance(node, dict):
        for key in ("item", "items", "data", "records", "list"):
            if key in node:
                found = _flatten_items(node[key])
                if found:
                    return found
        for value in node.values():
            if isinstance(value, (dict, list)):
                found = _flatten_items(value)
                if found:
                    return found
        if node and all(not isinstance(v, (dict, list)) for v in node.values()):
            return [node]
    return []


def _decode(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(encoding), "utf-8" if encoding == "utf-8-sig" else encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("파일 인코딩을 UTF-8 / CP949 로 읽을 수 없다")


def read_kc_records(
    path: Path, *, mapping: Mapping[str, list[str]] | None = None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """CSV / JSON / XML 파일을 읽어 표준 필드의 레코드 목록으로 만든다."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".csv", ".json", ".xml"):
        raise ValueError(f"지원하지 않는 형식: {suffix} (csv/json/xml)")
    raw = path.read_bytes()
    if suffix == ".xml" and len(raw) > _MAX_XML_BYTES:
        raise ValueError("XML 파일이 너무 크다")
    text, encoding = _decode(raw)

    rows: list[dict[str, Any]]
    if suffix == ".csv":
        rows = list(csv.DictReader(io.StringIO(text)))
    elif suffix == ".json":
        rows = _flatten_items(json.loads(text))
    else:
        root = ET.fromstring(text)
        rows = [{child.tag: (child.text or "").strip() for child in item} for item in root.iter("item")]
        if not rows:  # item 태그가 없는 단순 XML
            rows = [{child.tag: (child.text or "").strip() for child in node} for node in root if len(node)]

    mapping = {**DEFAULT_MAPPING, **(mapping or {})}
    records: list[dict[str, Any]] = []
    for row in rows:
        derived_raw = _pick(row, mapping["derived"])
        records.append({
            "model": _text(_pick(row, mapping["model"])),
            "derived": [d.strip() for d in _SPLIT.split(str(derived_raw)) if d.strip()] if derived_raw else [],
            "manufacturer": _text(_pick(row, mapping["manufacturer"])),
            "company": _text(_pick(row, mapping["company"])),
            "equipment": _text(_pick(row, mapping["equipment"])),
            "management_no": _text(_pick(row, mapping["management_no"])),
            "date": _text(_pick(row, mapping["date"])),
            "country": _text(_pick(row, mapping["country"])),
        })
    if rows and all(r["model"] is None for r in records):
        raise ValueError(
            "모델 열을 찾지 못했다. 파일의 열 이름: " + ", ".join(rows[0].keys()) + " — mapping 으로 '모델' 열 이름을 알려 준다"
        )
    return records, {"format": suffix[1:], "encoding": encoding, "rows": len(rows)}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


@dataclass
class ImportResult:
    entries: list[dict[str, Any]]
    report: dict[str, Any] = field(default_factory=dict)


def _requires_brand(code: str) -> bool:
    """짧거나 글자만/숫자만인 코드는 다른 글의 말과 우연히 겹치기 쉽다."""
    return len(code) < 6 or code.isalpha() or code.isdigit()


def _brand_for(manufacturer: str | None, company: str | None, lexicon: BrandLexicon, unmapped: Counter) -> str | None:
    for name in (manufacturer, company):
        if not name:
            continue
        found = lexicon.detect(name)
        if found:
            return found[0]
    name = manufacturer or company
    if not name:
        return None
    unmapped[name] += 1
    return compact_code(name) or None


def build_entries(records: Iterable[Mapping[str, Any]], lexicon: BrandLexicon) -> ImportResult:
    records = list(records)
    report: dict[str, Any] = {
        "records": len(records), "skipped_empty_model": 0, "skipped_too_short": 0, "skipped_no_manufacturer": 0,
        "dropped_aliases": [], "conflicts": [],
    }
    unmapped: Counter[str] = Counter()
    groups: dict[tuple[str, str], dict[str, Any]] = {}

    for rec in records:
        model = rec.get("model")
        if not model:
            report["skipped_empty_model"] += 1
            continue
        code = compact_code(model)
        if len(code) < MIN_CODE_LEN:
            report["skipped_too_short"] += 1
            continue
        brand = _brand_for(rec.get("manufacturer"), rec.get("company"), lexicon, unmapped)
        if brand is None:
            report["skipped_no_manufacturer"] += 1
            continue
        group = groups.setdefault((brand, code), {
            "brand": brand, "code": code, "model": model, "aliases": {}, "management_numbers": [], "manufacturers": set(),
            "equipment": set(), "dates": [], "countries": set(),
        })
        for derived in rec.get("derived") or []:
            if compact_code(derived) and compact_code(derived) != code:
                group["aliases"].setdefault(compact_code(derived), derived)
        if rec.get("management_no") and rec["management_no"] not in group["management_numbers"]:
            group["management_numbers"].append(rec["management_no"])
        for key, field_name in (("manufacturers", "manufacturer"), ("equipment", "equipment"), ("countries", "country")):
            if rec.get(field_name):
                group[key].add(rec[field_name])
        if rec.get("date"):
            group["dates"].append(rec["date"])

    # 같은 코드를 서로 다른 제조사가 주장하면 어느 쪽인지 알 수 없으므로 둘 다 제외한다.
    by_code: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key in groups:
        by_code[key[1]].append(key)
    excluded: set[tuple[str, str]] = set()
    for code, keys in by_code.items():
        if len({k[0] for k in keys}) > 1:
            excluded.update(keys)
            report["conflicts"].append({"code": code, "brands": sorted({k[0] for k in keys}), "reason": "same code under different manufacturers"})

    kept = {k: g for k, g in groups.items() if k not in excluded}
    base_codes = {k[1]: k for k in kept}
    # 같은 파생모델 코드를 서로 다른 항목이 별칭으로 주장하면 어느 쪽인지 알 수 없다.
    alias_claims: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key, g in kept.items():
        for alias_code in g["aliases"]:
            alias_claims[alias_code].append(key)
    contested = {code for code, keys in alias_claims.items() if len(keys) > 1}
    entries: list[dict[str, Any]] = []
    for (brand, code), g in sorted(kept.items()):
        aliases: list[str] = []
        for alias_code, alias_text in sorted(g["aliases"].items()):
            if alias_code in contested:
                report["dropped_aliases"].append({"alias": alias_text, "entry": f"kc:{brand}:{code}", "reason": "claimed as alias by several entries"})
                continue
            owner = base_codes.get(alias_code)
            if owner is not None and owner != (brand, code):
                report["dropped_aliases"].append({"alias": alias_text, "entry": f"kc:{brand}:{code}", "reason": f"is the base model of kc:{owner[0]}:{owner[1]}"})
                continue
            if alias_code in by_code and any(k in excluded for k in by_code[alias_code]):
                report["dropped_aliases"].append({"alias": alias_text, "entry": f"kc:{brand}:{code}", "reason": "alias code is in conflict"})
                continue
            aliases.append(alias_text)
        entries.append({
            "id": f"kc:{brand}:{code}", "brand": brand, "line": "", "model": g["model"],
            "category": "; ".join(sorted(g["equipment"])), "aliases": aliases, "verified": True, "source": "kc",
            "requires_brand": _requires_brand(code),
            "kc": {
                "management_numbers": g["management_numbers"], "manufacturers": sorted(g["manufacturers"]),
                "countries": sorted(g["countries"]), "first_date": min(g["dates"]) if g["dates"] else None,
            },
        })

    report.update(entries=len(entries), unmapped_manufacturers=dict(unmapped.most_common()))
    return ImportResult(entries, report)


def merge_with_curated(
    kc_entries: list[dict[str, Any]],
    curated: list[dict[str, Any]],
    alias_rows: Iterable[tuple[str, str]],
) -> ImportResult:
    """검수한 카탈로그와 KC 항목을 별칭 파일로 잇는다. 검수 항목이 우선한다.

    alias_rows: (catalog_id, alias). alias 가 KC 모델 코드면 그 KC 항목을 검수 항목에 흡수한다
    (코드와 파생모델이 별칭이 되고, 관리번호 등 인증 정보가 붙는다). 마케팅 이름이면 별칭만 더한다.
    """
    report: dict[str, Any] = {"alias_unknown_catalog_id": [], "alias_without_kc": [], "absorbed": []}
    curated_by_id = {c["id"]: c for c in curated}
    kc_by_code: dict[str, dict[str, Any]] = {}
    for entry in kc_entries:
        for code in {compact_code(entry["model"]), *(compact_code(a) for a in entry.get("aliases", []))}:
            kc_by_code[code] = entry

    absorbed_ids: set[str] = set()
    for catalog_id, alias in alias_rows:
        target = curated_by_id.get(catalog_id)
        if target is None:
            report["alias_unknown_catalog_id"].append({"catalog_id": catalog_id, "alias": alias})
            continue
        aliases = target.setdefault("aliases", [])
        if alias not in aliases:
            aliases.append(alias)
        source_entry = kc_by_code.get(compact_code(alias))
        if source_entry is None:
            report["alias_without_kc"].append({"catalog_id": catalog_id, "alias": alias})
            continue
        if source_entry["id"] in absorbed_ids:
            continue
        absorbed_ids.add(source_entry["id"])
        for code_text in [source_entry["model"], *source_entry.get("aliases", [])]:
            if code_text not in aliases:
                aliases.append(code_text)
        info = target.get("kc") or {"management_numbers": [], "manufacturers": [], "countries": [], "first_date": None}
        src = source_entry.get("kc") or {}
        info["management_numbers"] = sorted(set(info["management_numbers"]) | set(src.get("management_numbers", [])))
        info["manufacturers"] = sorted(set(info["manufacturers"]) | set(src.get("manufacturers", [])))
        info["countries"] = sorted(set(info["countries"]) | set(src.get("countries", [])))
        info["first_date"] = min([d for d in (info["first_date"], src.get("first_date")) if d] or [None]) if (info["first_date"] or src.get("first_date")) else None
        target["kc"] = info
        report["absorbed"].append({"kc_id": source_entry["id"], "into": catalog_id})

    remaining = [e for e in kc_entries if e["id"] not in absorbed_ids]
    return ImportResult([*curated_by_id.values(), *remaining], report)


def write_catalog(path: Path, entries: list[dict[str, Any]]) -> None:
    payload = {
        "_comment": "자동 생성 카탈로그. kc_import 로 공공 인증 DB 에서 만들었다. 직접 고치지 말고 입력 파일/별칭 파일을 고쳐 다시 만든다.",
        "products": entries,
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
