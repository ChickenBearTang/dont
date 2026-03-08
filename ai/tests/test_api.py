from __future__ import annotations

from fastapi.testclient import TestClient

from consumption_poc.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_index_served() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "AI 소비 리포트 대시보드" in response.text


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


def test_consumption_report_by_name() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/consumption-report",
        params={"user_name": "Lee Ji", "start": "2026-01", "end": "2026-03", "include_ai": "false"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["user_id"] == "U1002"
    assert payload["meta"]["user_name"] == "Lee Ji"


def test_list_users() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["users"]) == 8
    assert {"user_id": "U1002", "name": "Lee Ji"} in payload["users"]


def test_regenerate_endpoint() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/reports/regenerate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "consumption_report_summary.json" in payload["generated_files"]


def test_mock_consumption_stats_endpoint() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/mock-consumption-stats",
        params={"user_name": "Kim Minsoo", "month": "2026-02"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["user_id"] == "U1001"
    assert payload["period_summary"]["selected_month"] == "2026-02"
    assert payload["period_summary"]["current_total_spend"] == 1135300
    assert len(payload["daily_cumulative"]) > 20
    assert len(payload["category_breakdown"]) > 0
