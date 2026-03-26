from __future__ import annotations

import unittest

from ..xai.counterfactuals import CounterfactualEngine
from ..xai.dice_engine import DiceCounterfactualEngine


class DiceCounterfactualEngineTest(unittest.TestCase):
    def test_suggest_returns_dice_runtime_metadata_without_index_error(self) -> None:
        engine = DiceCounterfactualEngine(fallback_engine=CounterfactualEngine())

        suggestions, meta = engine.suggest(
            price_int=2_500_000,
            monthly_spending_30d=2_500_000.0,
            emergency_fund_balance=800_000.0,
            current_balance=3_000_000.0,
            days_until_card_due=12,
            expected_card_payment_amount=250_000.0,
        )

        self.assertGreaterEqual(len(suggestions), 1)
        self.assertTrue(meta.get("enabled"))
        self.assertEqual(meta.get("backend"), "dice_ml")


if __name__ == "__main__":
    unittest.main()
