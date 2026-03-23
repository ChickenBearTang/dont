# AI-Backend-Frontend 통합 로드맵 (TODO)

본 로드맵은 "DB 데이터의 실제 연동"을 최우선으로 하며, 이후의 안정화와 고도화로 이어지는 3단계 페이즈를 제안합니다.

---

### 🚀 Phase 1: 실제 DB 데이터 연동 (Core Data Sync)
**목표:** AI 서버가 로컬 파일을 전혀 보지 않고, 오직 백엔드가 DB에서 긁어온 데이터만으로 분석을 수행하게 함.

- [ ] **백엔드: 사용자 프로필(User Profile) 데이터 연동**
  - **Source**: [users](cci:1://file:///c:/Users/SSAFY/gomtang/S14P21A605/ai/src/api/v1/routers/consumption.py:7:0-9:42) 테이블
  - **Data**: `monthly_income`(월 수입), `pay_day`(급여일) 등을 [getAiAnalysis](cci:1://file:///c:/Users/SSAFY/gomtang/S14P21A605/backend/src/main/java/com/ssafy/edu/awesomeproject/domain/fin/card/service/CardService.java:192:4-246:5) 호출 시 `user_profile` 필드로 전달.
- [ ] **백엔드: 계좌 내역(Account Transactions) 필터링 및 전달**
  - **Source**: [account_transactions](cci:1://file:///c:/Users/SSAFY/gomtang/S14P21A605/ai/src/domain/consumption/reporting.py:39:0-42:104) 테이블
  - **Logic**: 분석 기간(`start_date`, `end_date`)에 해당하는 거래 내역을 모두 조회하여 AI 서버의 [account_transactions](cci:1://file:///c:/Users/SSAFY/gomtang/S14P21A605/ai/src/domain/consumption/reporting.py:39:0-42:104) 필드로 전달.
- [ ] **백엔드: 소명(Justification) 내역 DB 연동**
  - **Source**: `spending_justifications` (가칭) 테이블
  - **Action**: 유저가 사전에 입력한 소명 내역이 있다면, AI 호출 시 함께 전달하여 분석에 반영되도록 요청 모델 업데이트.
- [ ] **AI 서버: 데이터 포맷 정합성 테스트**
  - 백엔드에서 전송한 날짜(`YYYY-MM-DD`, `HH:MM:SS`) 및 금액 타입이 분석 로직 내부의 `INTERNAL_*` 클래스와 정확히 매칭되는지 최종 검증.

---

### 🛠 Phase 2: 서비스 안정화 및 운영 (Stabilization)
**목표:** 실제 서비스 환경에서 발생할 수 있는 장애 상황과 사용자 경험(UX)을 관리함.

- [ ] **백엔드: AI 서버 장애 상황 핸들링**
  - AI 서버 타임아웃(Timeout) 설정 및 응답 실패 시 리포트 페이지가 중단되지 않도록 예외 처리 로직 고도화.
- [ ] **프론트엔드: 분석 중 로딩 상태(Loading UI) 구현**
  - AI 분석은 LLM 연산으로 인해 시간이 걸릴 수 있으므로, "AI 분석 보고서를 작성 중입니다..."와 같은 특화된 로딩 인디케이터 적용.
- [ ] **인프라: 환경별 엔드포인트 분리**
  - `application-prod.yml` 파일에서 도커/쿠버네티스 내부망 AI 서버 주소(`ai-server:8000`) 환경변수 설정.

---

### 💎 Phase 3: 분석 고도화 (Advanced Optimization)
**목표:** 분석 결과의 품질을 높이고 리소스 사용을 효율화함.

- [ ] **AI 서버: 분석 결과 캐싱 (Response Caching)**
  - 동일한 달의 거래 데이터가 변하지 않았다면, 이미 분석된 결과를 DB에 기록해 두었다가 즉시 반환하여 API 비용 및 시간 절감.
- [ ] **프롬프트 튜닝 (Prompt Engineering)**
  - 금융 도메인 지식을 바탕으로 `actionable_solutions`의 답변 질을 높이기 위한 리드 프롬프트(Lead Prompt) 최적화.
- [ ] **확장성 확보**: 대규모 분석 요청 시 큐(Queue)를 통한 비동기 처리 구조 검토.

---
**최종 업데이트:** 2026-03-22
