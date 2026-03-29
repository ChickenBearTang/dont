from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROOT_PARENT = ROOT.parent
if str(ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(ROOT_PARENT))

from ai.price_engine.allowlist import SCHEMA_VERSION, training_feature_names
from ai.price_engine.artifacts import save_price_model_artifact
from ai.price_engine.schema_models import PriceFeatureSnapshotRow
from ai.price_engine.split import time_based_split
from ai.price_engine.train_lgbm import train_mvp_v1_5


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError("snapshot_date must be a non-empty datetime string")
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _row_from_payload(payload: dict[str, Any]) -> PriceFeatureSnapshotRow:
    snapshot_date = _parse_datetime(payload.get("snapshot_date"))
    return PriceFeatureSnapshotRow(
        canonical_product_id=str(payload["canonical_product_id"]),
        variant_id=(
            str(payload["variant_id"]) if payload.get("variant_id") is not None else None
        ),
        seller_id=(str(payload["seller_id"]) if payload.get("seller_id") is not None else None),
        snapshot_date=snapshot_date,
        current_effective_price=float(payload["current_effective_price"]),
        avg_price_7d=(
            float(payload["avg_price_7d"]) if payload.get("avg_price_7d") is not None else None
        ),
        avg_price_30d=(
            float(payload["avg_price_30d"]) if payload.get("avg_price_30d") is not None else None
        ),
        min_price_30d=(
            float(payload["min_price_30d"]) if payload.get("min_price_30d") is not None else None
        ),
        max_price_30d=(
            float(payload["max_price_30d"]) if payload.get("max_price_30d") is not None else None
        ),
        price_volatility_30d=(
            float(payload["price_volatility_30d"])
            if payload.get("price_volatility_30d") is not None
            else None
        ),
        seller_count_same_product=float(payload["seller_count_same_product"]),
        release_age_days=float(payload["release_age_days"]),
        shipping_fee_mode_30d=(
            float(payload["shipping_fee_mode_30d"])
            if payload.get("shipping_fee_mode_30d") is not None
            else None
        ),
        price_vs_avg_7d=(
            float(payload["price_vs_avg_7d"]) if payload.get("price_vs_avg_7d") is not None else None
        ),
        price_vs_avg_30d=(
            float(payload["price_vs_avg_30d"])
            if payload.get("price_vs_avg_30d") is not None
            else None
        ),
        price_to_min_30d_gap=(
            float(payload["price_to_min_30d_gap"])
            if payload.get("price_to_min_30d_gap") is not None
            else None
        ),
        price_to_max_30d_gap=(
            float(payload["price_to_max_30d_gap"])
            if payload.get("price_to_max_30d_gap") is not None
            else None
        ),
        brand=str(payload["brand"]),
        category=str(payload["category"]),
        seller_type=str(payload["seller_type"]),
        availability_status=str(payload["availability_status"]),
        schema_version=str(payload.get("schema_version", SCHEMA_VERSION)),
    )


def _load_rows(path: Path) -> list[PriceFeatureSnapshotRow]:
    if not path.exists():
        raise FileNotFoundError(f"input file not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if text == "":
        raise ValueError("input file is empty")

    rows_raw: list[dict[str, Any]] = []
    if path.suffix.lower() == ".jsonl":
        for line in text.splitlines():
            line = line.strip()
            if line == "":
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise ValueError("each JSONL row must be an object")
            rows_raw.append(raw)
    else:
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("input JSON must be a list of objects")
        for raw in parsed:
            if not isinstance(raw, dict):
                raise ValueError("input JSON rows must be objects")
            rows_raw.append(raw)

    rows = [_row_from_payload(raw) for raw in rows_raw]
    if len(rows) == 0:
        raise ValueError("no valid training rows")
    return rows


def _parse_cutoff(raw: str | None) -> datetime | None:
    if raw is None or raw.strip() == "":
        return None
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Train price_engine LGBM model")
    parser.add_argument("--input", required=True, help="Path to JSON or JSONL snapshot rows")
    parser.add_argument("--output-dir", required=True, help="Directory to save model artifacts")
    parser.add_argument(
        "--target-name",
        default="current_effective_price",
        help="Target column name in PriceFeatureSnapshotRow",
    )
    parser.add_argument(
        "--cutoff-date",
        default=None,
        help="Optional ISO datetime cutoff for train/test split",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    rows = _load_rows(input_path)
    cutoff = _parse_cutoff(args.cutoff_date)

    train_rows = rows
    test_rows: list[PriceFeatureSnapshotRow] = []
    if cutoff is not None:
        split = time_based_split(rows, cutoff_date=cutoff)
        train_rows = split.train
        test_rows = split.test
        if len(train_rows) == 0:
            raise ValueError("time split produced empty train rows")

    model = train_mvp_v1_5(train_rows, target_name=args.target_name)

    extra_metadata: dict[str, Any] = {
        "train_row_count": len(train_rows),
        "test_row_count": len(test_rows),
        "total_row_count": len(rows),
    }
    if cutoff is not None:
        extra_metadata["cutoff_date"] = cutoff.isoformat()

    if len(test_rows) > 0:
        from sklearn.metrics import mean_absolute_error

        feature_names = list(training_feature_names())
        x_test = []
        y_test = []
        for row in test_rows:
            payload = asdict(row)
            x_test.append({name: payload[name] for name in feature_names})
            y_test.append(float(payload[args.target_name]))
        import pandas as pd

        x_test_df = pd.DataFrame(x_test, columns=feature_names)
        for category_name in ("brand", "category", "seller_type", "availability_status"):
            x_test_df[category_name] = x_test_df[category_name].astype("category")
        prediction = model.predict(x_test_df)
        extra_metadata["mae_test"] = float(mean_absolute_error(y_test, prediction))

    artifact = save_price_model_artifact(
        model=model,
        output_dir=output_dir,
        schema_version=SCHEMA_VERSION,
        feature_names=list(training_feature_names()),
        target_name=args.target_name,
        model_family="lightgbm_regressor",
        extra_metadata=extra_metadata,
    )
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "schema_version": artifact.metadata["schema_version"],
                "target_name": artifact.metadata["target_name"],
                "feature_count": len(artifact.metadata["feature_names"]),
                "train_row_count": artifact.metadata.get("train_row_count"),
                "test_row_count": artifact.metadata.get("test_row_count"),
                "mae_test": artifact.metadata.get("mae_test"),
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
