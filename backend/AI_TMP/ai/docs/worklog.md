# Worklog

## 2026-03-08

### 데이터

- raw 데이터를 8명, 6개월 규모로 확장
- 사용자별 카드 결제/계좌 입출금 정합성 보정
- `generate_mock_raw_data.py` 스크립트 추가

### 통계

- 기본 소비 리포트 집계 파이프라인 구현
- 이상탐지 규칙 구현
- 사용자별/월별 목업 통계 산출물 추가

### AI

- Gemini API 연동
- 모델 fallback 처리
- `llm_status` 기반 degraded fallback 유지

### API

- `/api/v1/users`
- `/api/v1/consumption-report`
- `/api/v1/mock-consumption-stats`
- `/api/v1/reports/regenerate`

### 프론트

- 종합 대시보드 시도 후, 실제 목업 기준 월간 통계 화면으로 재구성
- 월별 소비, 전월 비교, 6개월 평균, 카테고리별 소비 시각화 구현
- AI 분석 섹션 재부착

### 검증

- pytest 통과
- Playwright로 페이지 로드 및 월간 통계/AI 분석 렌더링 확인

## 2026-03-08 Documentation Overhaul

### 문서

- `ai/README.md`를 프로젝트 개요 문서로 전면 재작성
- `docs/architecture.md`에 모듈 책임과 데이터 흐름 시각화 추가
- `docs/data-contract.md`에 raw/generated 경계와 카테고리 재분류 규칙 정리
- `docs/api-spec.md`에 프론트와 API 관계도 추가
- `docs/onboarding.md`를 새로 추가해 초심자용 읽기 순서와 디버깅 경로 정리
- `data/README.md`에 데이터 흐름 도식과 재생성 원칙 추가

### 목표

- 프로젝트를 처음 보는 사람도 코드 진입 전에 전체 구조를 이해할 수 있게 만들기
- 통계 계산, 이상탐지, AI 해설, 프론트 표시의 책임 경계를 명확히 설명하기
- 문제 발생 시 어디부터 봐야 하는지 문서만으로 안내하기
