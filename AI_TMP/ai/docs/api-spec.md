# API Specification

## 개요

이 서비스는 두 종류의 API를 제공한다.

- 기본 소비 리포트 API
  - 종합 리포트 + AI 해설
- 목업 통계 API
  - 월간 소비 화면용 통계

## 1. `GET /health`

헬스체크.

응답:

```json
{
  "status": "ok"
}
```

## 2. `GET /api/v1/users`

회원 목록 조회.

응답:

```json
{
  "users": [
    {
      "user_id": "U1001",
      "name": "Kim Minsoo"
    }
  ]
}
```

## 3. `POST /api/v1/reports/regenerate`

raw 기준으로 generated 산출물을 재생성한다.

응답:

```json
{
  "status": "ok",
  "generated_files": [
    "consumption_report_monthly.csv",
    "users/U1001/2026-02/period_summary.json"
  ]
}
```

## 4. `GET /api/v1/consumption-report`

종합 소비 리포트 + AI 분석.

쿼리:

- `user_id` optional
- `user_name` optional
- `start` required
- `end` required
- `include_ai` optional, default `true`

규칙:

- `user_id` 또는 `user_name` 중 하나는 반드시 있어야 한다.
- 둘 다 있으면 같은 사용자를 가리켜야 한다.

응답 구조:

```json
{
  "meta": {
    "user_id": "U1001",
    "user_name": "Kim Minsoo",
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

## 5. `GET /api/v1/mock-consumption-stats`

목업 화면 전용 월간 통계 API.

쿼리:

- `month` required
- `user_id` optional
- `user_name` optional

응답 구조:

```json
{
  "meta": {
    "user_id": "U1001",
    "user_name": "Kim Minsoo",
    "selected_month": "2026-02",
    "generated_at": "2026-03-08T00:00:00Z"
  },
  "period_summary": {
    "selected_month": "2026-02",
    "current_total_spend": 1135300,
    "previous_month": "2026-01",
    "previous_total_spend": 195500,
    "difference_amount": 939800,
    "difference_direction": "increase",
    "difference_text": "전월과 비교해 939,800원 더 썼어요"
  },
  "daily_cumulative": [],
  "six_month_trend": {
    "average_amount": 803788,
    "months": []
  },
  "category_breakdown": []
}
```

## 6. 프론트와 API 관계

```mermaid
flowchart LR
    A[index.html]
    B[/api/v1/users]
    C[/api/v1/mock-consumption-stats]
    D[/api/v1/consumption-report]

    A --> B
    A --> C
    A --> D
```

프론트는 현재:

- 회원 목록: `/api/v1/users`
- 목업 통계 화면: `/api/v1/mock-consumption-stats`
- AI 분석 섹션: `/api/v1/consumption-report`
