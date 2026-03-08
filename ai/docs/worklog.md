# 작업 로그

## 2026-03-08

- `feature/ai-consumption-poc` 브랜치 생성
- POC 범위, 데이터 계약, API 초안 문서화
- `data/raw`와 `data/generated` 구조 분리
- 카드대금 출금액이 월별 카드 사용 합계와 정확히 일치하도록 raw 계좌 데이터 정비
- 생성 파이프라인, 이상탐지, 서비스 레이어, API 골격 추가
- `.env`의 `GEMINI_API_KEY`를 읽는 로컬 설정 로직 추가
- raw 기준 generated 산출물 재생성 성공
- pytest 기반 로더, 정합성, API 테스트 추가
- `python -m pip install -e .[dev]`로 의존성 설치
- `python -m pytest -q` 실행 결과 10개 테스트 통과
- Gemini 경로는 `.env`를 통해 실제 호출되지만 현재 API quota 부족으로 `llm_status=degraded` fallback 동작 확인
- 다음 작업: 브랜치 정리 후 사용자 확인
