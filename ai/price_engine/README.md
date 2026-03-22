# price-engine-mvp-v1

MVP price engine package for unified price observations and phase1-safe training dataset generation.

## Key Rules
- Reserved coupon/card/membership fields are stored but excluded from phase1 training.
- Training columns are allowlist-only.
- Forbidden raw/url/id/source fields are blocked from training.
- Time split is mandatory (no random split).
- Rolling features use only past observations before each snapshot timestamp.
- Schema mismatch fails fast.

## Main Modules
- `schema_models.py`: raw/normalized schemas and snapshot row models
- `normalizer.py`: source-priority merge to `PriceObservation`
- `dataset_builder.py`: `price_feature_snapshot_v1` builder
- `schema_validator.py`: schema and field policy guards
- `split.py`: time-based split
- `train_lgbm.py`: MVP v1.5 LightGBM trainer (optional dependency)

## Run Tests
```bash
python3 -m unittest ai.tests.test_price_engine_schema ai.tests.test_price_engine_dataset ai.tests.test_price_engine_rolling ai.tests.test_price_engine_split
```
