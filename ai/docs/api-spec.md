# API 명세

## `GET /health`

서비스 상태를 반환한다.

### 응답

```json
{
  "status": "ok"
}
```

## `POST /api/v1/reports/regenerate`

raw 데이터를 기준으로 generated 산출물을 재생성한다.

### 응답

```json
{
  "status": "ok",
  "generated_files": [
    "consumption_report_monthly.csv",
    "consumption_report_category.csv",
    "consumption_report_time.csv",
    "consumption_report_anomalies.csv",
    "cashflow_report_monthly.csv",
    "consumption_report_summary.json"
  ]
}
```

## `GET /api/v1/consumption-report`

### 쿼리

- `user_id`
- `start`
- `end`
- `include_ai`

### 응답 구조

```json
{
  "meta": {
    "user_id": "U1001",
    "period": {
      "start": "2026-01",
      "end": "2026-03"
    },
    "generated_at": "2026-03-08T00:00:00Z",
    "llm_status": "ok"
  },
  "overview": {},
  "monthly": [],
  "categories": {
    "by_month": [],
    "top_categories": [],
    "top_subcategories": []
  },
  "time_patterns": {
    "time_bands": [],
    "weekdays": []
  },
  "cashflow": [],
  "anomalies": [],
  "ai_analysis": {
    "consumption_patterns": [],
    "anomaly_explanations": [],
    "actionable_solutions": []
  }
}
```
