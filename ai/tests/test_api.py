from __future__ import annotations

from fastapi.testclient import TestClient

from consumption_poc.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_consumption_report_without_ai() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/consumption-report",
        params={"user_id": "U1001", "start": "2026-01", "end": "2026-03", "include_ai": "false"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["llm_status"] == "skipped"
    assert payload["overview"]["total_card_spend"] == 1529100


def test_regenerate_endpoint() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/reports/regenerate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "consumption_report_summary.json" in payload["generated_files"]
