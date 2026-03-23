# XAI 완료 점검 체크리스트

## 0. 용어 정의 (반드시 고정)

- [x] 이 프로젝트에서 XAI는 외부 브랜드명이 아니라 **Explainable AI(설명 가능한 AI)** 를 의미한다
- [x] `--xai` 플래그는 Explainable AI 설명 페이로드 생성을 활성화한다
- [x] 기본 출력 계약은 `schema_version`, `explanations`, `analysis` 필드를 포함한다

## 1. 기본 실행 확인

### 1-1. mock 실행

```bash
python -m ai --xai --top-k 3
```

- [x] 명령이 에러 없이 실행된다
- [x] JSON 형식으로 출력된다
- [x] `schema_version` 필드가 존재한다
- [x] `analysis` 필드가 존재한다
- [x] `explanations` 필드가 list이다

### 1-2. real crawl 실행

```bash
python -m ai --xai --real-crawl --top-k 3
```

- [x] 명령이 에러 없이 실행된다
- [x] `item_count > 0`
- [x] explanation item이 실제 생성된다

## 2. 응답 스키마 확인

각 explanation item마다:

- [x] `decision` 존재
- [x] `decision_confidence` 존재
- [x] `reason_codes` 존재
- [x] `reason_texts` 존재
- [x] `supporting_evidence` 존재
- [x] `counterfactual_conditions` 존재
- [x] `user_options` 존재
- [x] `rule_version` 존재
- [x] `data_snapshot_id` 존재
- [x]  `reasons` 존재
- [x] `counterfactuals` 존재
- [x] `polished_summary` 존재
- [x] `errors` 존재

## 3. decision 값 검증

- [x] `decision` 값이 아래 집합 중 하나이다
  - [ ] `BUY_NOW`
  - [ ] `WAIT`
  - [ ] `REVIEW`
  - [ ] `NOT_RECOMMENDED`

- [ ] `BUY`, `SKIP` 같은 구형 label이 나오지 않는다

## 4. reason 개수 정책 확인

- [ ] `reason_codes` 개수가 4개 이하이다
- [ ] `reason_texts` 개수가 4개 이하이다
- [ ] `reasons` 개수가 4개 이하이다
- [ ] `top_k`를 크게 줘도 consumer-facing reason은 4개 이하이다

테스트 예시:

```bash
python -m ai --xai --real-crawl --top-k 10
```

## 5. 설명 품질 확인

각 item에 대해 수동 확인:

- [ ] `decision`과 `reason_texts` 내용이 서로 모순되지 않는다
- [ ] `reason_codes`와 `reason_texts`가 대응된다
- [ ] `supporting_evidence`가 실제 reason과 연결된다
- [ ] reason에 없는 feature가 evidence로 튀어나오지 않는다
- [ ] 없는 요인을 지어내지 않는다

예:

- [ ] coupon 정보가 없는데 coupon 관련 reason이 나오지 않는다
- [ ] finance 값이 없는데 finance explanation을 함부로 만들지 않는다

## 6. counterfactual 정책 확인

각 `counterfactual_conditions`에 대해:

- [ ] 허용된 변수만 사용한다
  - [ ] `current_effective_price`
  - [ ] `available_budget`
  - [ ] `emergency_buffer`

- [ ] 허용되지 않은 숨겨진 내부 변수는 사용하지 않는다
- [ ] threshold / suggested_change / message가 논리적으로 맞다

## 7. evidence grounding 확인

- [ ] explanation이 실제 사용된 점수/룰과 연결된다
- [ ] `supporting_evidence`가 실제 feature contribution 기반이다
- [ ] audit log의 `feature_contributions`와 explanation reason이 대응된다
- [ ] 설명 문장이 저장되지 않은 요인을 새로 만들지 않는다

## 8. audit / traceability 확인

`analysis.audit_logs`에 대해:

- [ ] `audit_logs` 필드가 존재한다
- [ ] 각 로그에 `model_input_vector_hash`가 있다
- [ ] 각 로그에 `feature_contributions`가 있다
- [ ] 각 로그에 `final_decision`이 있다
- [ ] 각 로그에 `model_version`이 있다
- [ ] 각 로그에 `rule_version`이 있다
- [ ] 각 로그에 `schema_version`이 있다
- [ ] 각 로그에 `data_snapshot_id`가 있다

## 9. 에러 처리 확인

malformed / missing item에 대해:

- [ ] 시스템이 전체 크래시하지 않는다
- [ ] 해당 item은 `REVIEW` 또는 에러 payload로 처리된다
- [ ] `errors` 필드에 적절한 코드가 남는다
- [ ] 실패 item이 있어도 나머지 item 분석은 계속된다

## 10. finance 영향 확인

finance 입력을 바꿔서 실행:

```bash
python -m ai --xai --real-crawl --current-balance 100000 --emergency-fund-balance 0
```

- [ ] 재무 상태 변화에 따라 decision이 바뀔 수 있다
- [ ] finance 관련 reason이 실제로 설명에 반영된다
- [ ] 설명과 decision 변화가 논리적으로 맞다

## 11. 테스트 통과 확인

```bash
python -m unittest discover -s ai/tests -p "test_*.py"
```

- [ ] 전체 테스트 통과
- [ ] `test_xai_schema` 통과
- [ ] `test_xai_reasoning` 통과
- [ ] `test_xai_analyzer` 통과
- [ ] `test_xai_policy_contract` 통과

## 12. DB 연동 확인(선택)

DB 포함 시:

```bash
pip install "psycopg[binary]==3.2.1"
python -m ai.crawler.run_workflow
```

- [ ] DB 연결 성공
- [ ] crawl 저장 성공
- [ ] window stats 읽기 성공
- [ ] XAI 실행과 DB 경로가 충돌하지 않음

## 최종 완료 판정

아래를 모두 만족하면 **XAI 기능 완료**로 판단:

- [ ] 실행 가능
- [ ] 스키마 완전
- [ ] decision label 정상
- [ ] reason cap 준수
- [ ] explanation 품질 양호
- [ ] evidence grounding 충족
- [ ] audit trace 가능
- [ ] 에러 처리 안정적
- [ ] 테스트 통과
- [ ] (운영 시) FastAPI/API 경로에서도 정상 동작
