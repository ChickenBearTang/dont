from __future__ import annotations

import tempfile
import unittest

from ..price_engine.artifacts import (
    load_price_model_artifact,
    save_price_model_artifact,
)


class _FakeModel:
    def __init__(self) -> None:
        self.payload = "ok"

    def predict(self, _):  # pragma: no cover - behavior tested via load/save
        return [1.0]


class PriceEngineArtifactsTest(unittest.TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            saved = save_price_model_artifact(
                model=_FakeModel(),
                output_dir=tmp_dir,
                schema_version="price-engine-mvp-v1",
                feature_names=["a", "b"],
                target_name="target",
                model_family="lightgbm_regressor",
                extra_metadata={"mae_test": 1.23},
            )
            self.assertEqual(saved.metadata["target_name"], "target")
            loaded = load_price_model_artifact(tmp_dir)
            self.assertEqual(loaded.metadata["schema_version"], "price-engine-mvp-v1")
            self.assertEqual(loaded.metadata["feature_names"], ["a", "b"])
            self.assertAlmostEqual(float(loaded.metadata["mae_test"]), 1.23, places=4)
            self.assertTrue(hasattr(loaded.model, "predict"))


if __name__ == "__main__":
    unittest.main()
