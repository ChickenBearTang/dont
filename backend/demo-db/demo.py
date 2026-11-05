#!/usr/bin/env python3
"""demo DB 생성·적재 도구 (표준 라이브러리 + psql).

    python3 backend/demo-db/demo.py summary                    # 가상 사용자 표를 본다
    python3 backend/demo-db/demo.py generate --out build       # 시드 .sql 두 개를 만든다
    python3 backend/demo-db/demo.py load --finance-dsn URL --crawl-dsn URL
    python3 backend/demo-db/demo.py unload --finance-dsn URL --crawl-dsn URL   # 데모 행만 지운다

전부 가짜 데이터다. 운영 DB 에 넣지 않는다 — DSN 의 호스트가 로컬이 아니면 --force 없이는 거부한다.
날짜는 --as-of(기본: 오늘) 기준 절대 날짜다. Spring 이 '최근 30일'·'이번 달'을 오늘로 계산하므로,
며칠 지나면 --as-of 를 오늘로 다시 적재한다 (같은 명령을 다시 돌리면 이전 데모 행만 지우고 새로 넣는다).
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo_data import crawl, finance  # noqa: E402

SCHEMA_DIR = ROOT / "schema"
DEFAULT_SEED = 7
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


# ------------------------------------------------------------------ 안전장치

def dsn_host(dsn: str) -> str | None:
    """DSN 의 호스트. 유닉스 소켓(호스트 미지정 또는 '/' 로 시작)이면 None."""
    text = dsn.strip()
    if re.match(r"^postgres(ql)?://", text):
        parsed = urlparse(text)
        query_host = parse_qs(parsed.query).get("host", [None])[0]
        host = query_host or parsed.hostname
    else:
        match = re.search(r"(?:^|\s)host\s*=\s*('(?:[^'\\]|\\.)*'|\S+)", text)
        host = match.group(1).strip("'") if match else None
    if not host or host.startswith("/"):
        return None
    return host


def is_local_dsn(dsn: str) -> bool:
    host = dsn_host(dsn)
    return host is None or host.lower() in LOCAL_HOSTS or host.lower().startswith("demo")


def require_safe(dsn: str, force: bool) -> None:
    if is_local_dsn(dsn) or force:
        return
    raise SystemExit(
        f"거부: DSN 호스트 '{dsn_host(dsn)}' 는 로컬/demo 호스트가 아니다. 이 도구는 가짜 데이터를 넣고 "
        "이전 데모 행을 지운다. 정말 이 DB 가 데모용이면 --force 를 붙인다."
    )


# ------------------------------------------------------------------ 렌더링

def render(as_of: date, seed: int) -> dict[str, str]:
    return {
        "finance_seed.sql": finance.seed_sql(as_of, seed),
        "crawl_seed.sql": crawl.seed_sql(as_of, seed),
    }


def psql(dsn: str, *, sql: str | None = None, file: Path | None = None) -> None:
    command = ["psql", "--dbname", dsn, "-X", "-q", "-v", "ON_ERROR_STOP=1"]
    if file is not None:
        command += ["-f", str(file)]
        stdin = None
    else:
        command += ["-f", "-"]
        stdin = sql
    try:
        result = subprocess.run(command, input=stdin, text=True, capture_output=True)
    except FileNotFoundError:
        raise SystemExit("psql 을 찾을 수 없다 (PostgreSQL 클라이언트가 필요하다)")
    if result.returncode != 0:
        raise SystemExit(f"psql 실패 (exit {result.returncode}):\n{result.stderr.strip()}")


def apply_finance(dsn: str, as_of: date, seed: int) -> None:
    psql(dsn, file=SCHEMA_DIR / "finance_schema.sql")
    psql(dsn, sql=finance.seed_sql(as_of, seed))


def apply_crawl(dsn: str, as_of: date, seed: int) -> None:
    psql(dsn, file=SCHEMA_DIR / "crawl_items_schema.sql")
    psql(dsn, sql=crawl.seed_sql(as_of, seed))


# ------------------------------------------------------------------ 명령

def _won(value: int) -> str:
    return f"{value:,}"


def cmd_summary(args: argparse.Namespace) -> None:
    as_of = args.as_of
    print(f"as_of={as_of.isoformat()} seed={args.seed}  (기대 상태는 {_won(finance.TYPICAL_PRICE)}원 구매 기준)\n")
    header = ("id", "소득", "고정지출", "30일카드", "건수", "연결계좌", "세이브박스", "기대", "설명")
    print(" | ".join(header))
    for profile in finance.PROFILES:
        user = finance.build_user(profile, as_of, args.seed)
        primary = user.final_balance.get("P")
        savebox = user.final_balance.get("S")
        print(
            " | ".join(
                [
                    profile.key,
                    _won(profile.income),
                    _won(profile.fixed_expense),
                    _won(sum(t.amount for t in user.card_tx if (as_of - t.on).days < 30)),
                    str(sum(1 for t in user.card_tx if (as_of - t.on).days < 30)),
                    "-" if primary is None else _won(primary),
                    "-" if savebox is None else _won(savebox),
                    profile.expected_budget,
                    profile.label,
                ]
            )
        )


def cmd_generate(args: argparse.Namespace) -> None:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in render(args.as_of, args.seed).items():
        (out / name).write_text(text, encoding="utf-8")
        print(f"{out / name}  ({len(text.encode('utf-8')):,} bytes)")


def cmd_load(args: argparse.Namespace) -> None:
    if not args.finance_dsn and not args.crawl_dsn:
        raise SystemExit("--finance-dsn 또는 --crawl-dsn 중 하나는 필요하다")
    for dsn in (args.finance_dsn, args.crawl_dsn):
        if dsn:
            require_safe(dsn, args.force)
    if args.finance_dsn:
        apply_finance(args.finance_dsn, args.as_of, args.seed)
        print(f"finance: 적재 완료 (as_of={args.as_of.isoformat()}, 사용자 {len(finance.PROFILES)}명)")
    if args.crawl_dsn:
        apply_crawl(args.crawl_dsn, args.as_of, args.seed)
        print(f"crawl: 적재 완료 (as_of={args.as_of.isoformat()}, 제품 {len(crawl.PRODUCTS)}개)")


def cmd_unload(args: argparse.Namespace) -> None:
    if not args.finance_dsn and not args.crawl_dsn:
        raise SystemExit("--finance-dsn 또는 --crawl-dsn 중 하나는 필요하다")
    for dsn in (args.finance_dsn, args.crawl_dsn):
        if dsn:
            require_safe(dsn, args.force)
    if args.finance_dsn:
        psql(args.finance_dsn, sql=f"BEGIN;\n{finance.cleanup_sql()}\nCOMMIT;\n")
        print("finance: 데모 행 삭제 (코호트 DEMO 는 남김)")
    if args.crawl_dsn:
        psql(args.crawl_dsn, sql=f"BEGIN;\n{crawl.cleanup_sql()}\nCOMMIT;\n")
        print("crawl: 데모 행 삭제")


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"YYYY-MM-DD 형식이어야 한다: {value}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="demo DB 생성·적재 (전부 가짜 데이터)")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser, *, dsn: bool) -> None:
        if not dsn:
            p.add_argument("--as-of", type=_date, default=None, help="기준일(기본: 오늘)")
            p.add_argument("--seed", type=int, default=DEFAULT_SEED)
        if dsn:
            p.add_argument("--finance-dsn", help="Spring 본 DB 용 DSN (postgresql://… 또는 'host=… dbname=…')")
            p.add_argument("--crawl-dsn", help="ai-postgres(crawl_items) 용 DSN")
            p.add_argument("--force", action="store_true", help="로컬/demo 호스트가 아니어도 진행")

    summary = sub.add_parser("summary", help="가상 사용자 표")
    common(summary, dsn=False)
    summary.set_defaults(func=cmd_summary)

    generate = sub.add_parser("generate", help="시드 .sql 생성")
    common(generate, dsn=False)
    generate.add_argument("--out", default=str(ROOT / "build"))
    generate.set_defaults(func=cmd_generate)

    load = sub.add_parser("load", help="스키마 + 시드 적재 (이전 데모 행은 먼저 지움)")
    common(load, dsn=False)
    common(load, dsn=True)
    load.set_defaults(func=cmd_load)

    unload = sub.add_parser("unload", help="데모 행만 삭제")
    common(unload, dsn=True)
    unload.set_defaults(func=cmd_unload)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if hasattr(args, "as_of") and args.as_of is None:
        args.as_of = date.today()
    args.func(args)


if __name__ == "__main__":
    main()
