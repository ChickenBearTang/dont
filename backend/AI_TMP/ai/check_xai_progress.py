from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import importlib
import json
from typing import Any

from ai.manager import AIPipelineManager
from ai.models import CrawlResult, HotDeal
from ai.xai.analyzer import ExplainabilityAnalyzer


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: dict[str, Any]


class _SampleCrawler:
    def crawl(self) -> CrawlResult:
        return CrawlResult(
            source="progress-check",
            fetched_at=datetime.now(timezone.utc),
            items=[
                HotDeal(
                    title="Sample Deal",
                    url="https://example.com/deal/1",
                    price="129000",
                )
            ],
        )


def _import_checks() -> CheckResult:
    modules = [
        "ai.manager",
        "ai.__main__",
        "ai.xai.analyzer",
        "ai.storage.postgres_store",
        "ai.crawler.run_workflow",
    ]
    loaded: list[str] = []
    for module_name in modules:
        importlib.import_module(module_name)
        loaded.append(module_name)
    return CheckResult(name="imports", ok=True, details={"loaded_modules": loaded})


def _manager_checks() -> CheckResult:
    manager = AIPipelineManager(crawler=_SampleCrawler())
    legacy_result = manager.run()

    soft_fail_manager = AIPipelineManager(
        crawler=_SampleCrawler(),
        analyzer=lambda _: (_ for _ in ()).throw(RuntimeError("forced")),
        analyzer_soft_fail=True,
    )
    fallback_result = soft_fail_manager.run()

    ok = isinstance(legacy_result, CrawlResult) and isinstance(fallback_result, dict)
    return CheckResult(
        name="manager",
        ok=ok,
        details={
            "legacy_payload_shape": {
                "source": getattr(legacy_result, "source", None),
                "item_count": len(getattr(legacy_result, "items", [])),
            },
            "fallback_keys": sorted(list(fallback_result.keys()))
            if isinstance(fallback_result, dict)
            else [],
        },
    )


def _analyzer_checks() -> CheckResult:
    analyzer = ExplainabilityAnalyzer()
    payload = analyzer.analyze_crawl_result(_SampleCrawler().crawl(), top_k=3)
    required_keys = {
        "schema_version",
        "analyzer_id",
        "generated_at",
        "model_version",
        "crawl",
        "errors",
        "statistics",
        "finance_profile",
        "rule_version",
        "audit_logs",
        "runtime_engines",
    }
    missing = sorted(list(required_keys - set(payload.keys())))
    return CheckResult(
        name="xai_analyzer",
        ok=len(missing) == 0,
        details={
            "missing_keys": missing,
            "schema_version": payload.get("schema_version"),
            "analyzer_id": payload.get("analyzer_id"),
        },
    )


def run_progress_checks() -> dict[str, Any]:
    checks: list[CheckResult] = []
    failures: list[dict[str, Any]] = []

    for check in (_import_checks, _manager_checks, _analyzer_checks):
        try:
            result = check()
        except Exception as exc:  # pragma: no cover - defensive summary path
            result = CheckResult(
                name=check.__name__,
                ok=False,
                details={"error": str(exc)},
            )
        checks.append(result)
        if not result.ok:
            failures.append({"name": result.name, "details": result.details})

    return {
        "ok": len(failures) == 0,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": [
            {"name": check.name, "ok": check.ok, "details": check.details}
            for check in checks
        ],
        "failures": failures,
    }


def main() -> None:
    print(json.dumps(run_progress_checks(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
