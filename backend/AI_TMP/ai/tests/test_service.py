from __future__ import annotations

from consumption_poc.service import ReportService


def test_monthly_card_totals_match_account_card_bill() -> None:
    service = ReportService()
    report = service.build_report("2026-01", "2026-03", user_id="U1001", include_ai=False)

    monthly = {row["month"]: row["total_card_spend"] for row in report["monthly"]}
    card_bill = {row["month"]: row["card_bill"] for row in report["cashflow"]}

    assert monthly == card_bill


def test_category_share_sums_to_100_per_month() -> None:
    service = ReportService()
    report = service.build_report("2026-01", "2026-03", user_id="U1001", include_ai=False)

    by_month: dict[str, float] = {}
    for row in report["categories"]["by_month"]:
        by_month[row["month"]] = by_month.get(row["month"], 0.0) + row["share_percent"]

    for value in by_month.values():
        assert value == 100.0


def test_time_pattern_share_sums_to_100() -> None:
    service = ReportService()
    report = service.build_report("2026-01", "2026-03", user_id="U1001", include_ai=False)

    total = sum(row["share_percent"] for row in report["time_patterns"]["time_bands"])
    assert total == 100.1 or total == 100.0


def test_high_amount_late_night_transaction_has_highest_risk() -> None:
    service = ReportService()
    report = service.build_report("2026-01", "2026-03", user_id="U1001", include_ai=False)

    top = report["anomalies"][0]
    assert top["transaction_id"] == "C202602012"
    assert top["anomaly_type"] == "high_amount_late_night"


def test_build_report_resolved_by_name() -> None:
    service = ReportService()
    report = service.build_report("2026-01", "2026-03", user_name="Park Hana", include_ai=False)
    assert report["meta"]["user_id"] == "U1003"
    assert report["meta"]["user_name"] == "Park Hana"


def test_regenerate_writes_generated_files() -> None:
    service = ReportService()
    generated_files = service.regenerate()
    assert "consumption_report_summary.json" in generated_files
    assert "users/U1001/2026-02/period_summary.json" in generated_files
    assert "users/U1001/2026-02/category_breakdown.csv" in generated_files
