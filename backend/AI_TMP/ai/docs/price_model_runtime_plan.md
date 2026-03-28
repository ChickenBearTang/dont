## Price Model Runtime Plan (Phase 1)

### 1) Gate Decision
- Scope: connect the existing `price_engine` LightGBM model to the production PR XAI flow.
- Phase 1 target: `current_effective_price` (kept for compatibility with existing training rows).
- Decision policy: financial stress rules remain rule-based; only price signal is hybridized with model output.

### 2) Data Contract (Training/Inference Shared)
- Source of truth: `price_engine/allowlist.py` (`FEATURE_ALLOWLIST_PHASE1`).
- Numeric features:
  - `current_effective_price`
  - `avg_price_7d`
  - `avg_price_30d`
  - `min_price_30d`
  - `max_price_30d`
  - `price_volatility_30d`
  - `seller_count_same_product`
  - `release_age_days`
  - `shipping_fee_mode_30d`
  - `price_vs_avg_7d`
  - `price_vs_avg_30d`
  - `price_to_min_30d_gap`
  - `price_to_max_30d_gap`
- Categorical features:
  - `brand`
  - `category`
  - `seller_type`
  - `availability_status`
- Inference gate:
  - Must pass `validate_inference_payload()`.
  - Any missing/unknown/forbidden field forces model fallback.

### 3) Runtime Safety Rules
- Model usage is opt-in by `AI_PRICE_MODEL_ENABLED=true`.
- Model path is read from `AI_PRICE_MODEL_PATH`.
- If model load/predict/validation fails, PR XAI must still return a normal response using legacy rule flow.
