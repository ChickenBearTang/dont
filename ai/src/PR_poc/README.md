# XAI Purchase Recommendation (PoC)

이 프로젝트는 소비자의 상품 구매 시 **가격 경쟁력(Price)** 과 **개인 재무 위험도(Finance)** 를 종합적으로 판단하여 구매 가이드를 제공하는 **개념 증명(Proof of Concept)** 스크립트입니다. 

머신러닝 모델의 예측 결과를 설명 가능하게(Explainable AI, XAI) 만들기 위해 **SHAP**(기여도 분석)와 **DiCE**(반사실적 조건 제시)를 접목했습니다.

---

## 🚀 주요 기능

1. **데이터 임의 생성 (Mocking)**
   - `make_price_data`: 시장 가격 평균, 재고, 쿠폰/배송비 등을 바탕으로 해당 상품이 'cheap(저렴한지)', 'normal(적당한지)', 'expensive(비싼지)' 분류하는 가상의 가격 데이터를 생성합니다.
   - `make_finance_data`: 개인의 월별 지출액, 여유 자금 지표, 비상금 규모 등을 기반으로 이번 소비가 가져올 재무적 위험을 'low(안전)', 'medium(주의)', 'high(위험)' 등으로 분류하는 가상의 재무 데이터를 생성합니다.

2. **모델 학습 엔진 (Training)**
   - 가격 분석 엔진: `CatBoostClassifier` 모델을 활용하여 다중 범주형 피처(브랜드, 판매자, 카테고리 등)가 섞인 데이터를 학습합니다.
   - 재무 분석 엔진: `LightGBM` 범용 모델(트리 기반)을 활용하여 재무 위험도를 분류합니다.
   - DiCE 연동을 위한 재무 모델: 카테고리성 액션 가이드 변수 처리가 복잡한 DiCE의 특성을 고려하여 DiCE 파이프라인 전용으로 훈련되는 분리된 LightGBM 모델입니다.

3. **XAI (Explainable AI) 및 제안 엔진**
   - **엔진 룰베이스 의사결정**: 가격 분류 결과 기반의 예상 손실률(expected_drop_prob) 및 재무 모델의 예측을 결합해 최종 구매 결정 액션(`"HOLD", "BUY_NOW", "WAIT", "REVIEW"`)을 도출합니다.
   - **SHAP (기여도 분석)**: TreeExplainer를 통해 각 피처가 최종 예측값에 얼마나 기여했는지(긍정/부정)를 분석하고, 사전 정의된 텍스트(`REASON_CODE_MAP`) 룰과 결합하여 Top 3 설명 문구를 클라이언트에게 전달합니다. 
   - **DiCE (Counterfactual, 반사실적 설명)**: 현재 재무 위험도가 '높음(High)' 혹은 '중간(Medium)'으로 나왔을 때, **어떤 조건이 변경되면(예: 비상금 추가 확보, 혹은 현재 잔고 증가 등)** 다음 위험도(한 단계 낮은 클래스)로 낮출 수 있는지 역산하여 제안합니다.

---

## 🛠 필수 의존성 (Environment)

스크립트를 실행하려면 다음 패키지들이 설치되어 있어야 합니다. (Python 3.8 이상 권장)

```bash
pip install pandas numpy catboost lightgbm shap dice_ml
```

---

## ▶️ 실행 방법

메인 스크립트를 실행하면 1,500개의 임의 데이터를 즉흥적으로 생성하고 2개의 엔진 모델(CatBoost, LightGBM)을 학습한 뒤, 지정된(Sample) 1개의 쿼리에 대해 분석 및 XAI 예측을 수행합니다.

```bash
python initial.py
```

### 실행 결과 예시 (JSON Payload)

```json
{
  "decision": "REVIEW",
  "price_engine": {
    "price_bucket": "normal",
    "fair_price": 335040.0,
    "expected_drop_prob": 0.2856
  },
  "finance_engine": {
    "finance_risk_bucket": "low",
    "affordability_score": 0.658,
    "stress_score": 0.342
  },
  "reasons": [
    {
      "feature": "avg_price_30d",
      "shap_value": 0.4491,
      "reason_code": "PRICE_RELATIVE_TO_30D_AVG",
      "reason_text": "현재 가격이 최근 30일 평균과 비교해 유리하게 작용했습니다.",
      "source_type": "price_shap"
    },
    {
      "feature": "recent_30d_spending_growth_rate",
      "shap_value": 0.8123,
      "reason_code": "RECENT_SPENDING_SURGE",
      "reason_text": "최근 소비 증가로 재무 부담 가능성이 있습니다.",
      "source_type": "finance_shap"
    }
  ],
  "counterfactuals": [
    {
      "type": "fallback_counterfactual",
      "message": "비상자금을 약 550,000원 더 확보하면 재무 위험이 완화될 수 있습니다."
    }
  ]
}
```

---

## 💡 유의사항 및 개선 방향

현재 스크립트는 **개념 증명(PoC)** 단계이므로 실제 프로덕션 적용을 위해 다음의 개선이 필요합니다.

1. **모델 지속성 (Model Persistence)**: `initial.py`는 매번 실행마다 데이터를 생성하고 모델을 학습합니다. 추후 API 서버 구조로 전환하게 되면 `.pkl` 이나 `.joblib` 형태로 학습된 모델을 저장/로드(Save & Load)하는 파일 구조로 분리가 필요합니다.
2. **DiCE 카테고리 지원**: 현재 DiCE 전용 재무 모델은 Number형 자료만 취급하도록 간소화되어 있습니다. 향후 소비자 카테고리 구매 여부/플래그 변수에 대해 다채로운 제안을 생성하게 하려면 범주형 전처리 파이프라인 추가가 필요합니다.
