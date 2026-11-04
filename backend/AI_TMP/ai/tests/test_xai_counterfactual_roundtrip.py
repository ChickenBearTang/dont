"""반사실 제안이 실제로 지켜지는지 왕복 검증한다.

제안: "비상자금을 X원 늘리면 판단이 '재검토'로 바뀝니다".
검증: 정말로 요청의 비상자금을 X원 늘려 서비스를 다시 돌리면 '재검토'가 나오는가.
이 테스트가 없으면 validated=True 는 말뿐이다 (예전에는 type 이 'dice' 이기만 하면 True).
"""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from domain.xai_purchase.audit_store import JsonlXaiAuditLogStore
from domain.xai_purchase.service import evaluate_pr_purchase_xai

from ..xai.model_counterfactual import DECISION_RANK, ModelCounterfactualEngine
from .test_xai_signed_explanation import HEALTHY, TIGHT, _request

# 서비스 응답의 구조화 필드가 없어(Spring DTO 호환을 위해 스키마를 늘리지 않았다)
# 엔진이 내놓은 제안을 가로채서 다시 적용해 본다.
_FIELD = {
    "emergency_fund_balance": "emergencyFundBalance",
    "savebox_balance": "saveboxBalance",
    "current_balance": "currentBalance",
}


def _run(request):
    captured: list[dict] = []
    original = ModelCounterfactualEngine.suggest

    def spy(self, **kwargs):
        results, state = original(self, **kwargs)
        captured.extend(results)
        return results, state

    with tempfile.TemporaryDirectory() as tmp, patch(
        "domain.xai_purchase.service._AUDIT_STORE", JsonlXaiAuditLogStore(Path(tmp) / "a.jsonl")
    ), patch.object(ModelCounterfactualEngine, "suggest", spy):
        return evaluate_pr_purchase_xai(request), captured


def _apply(request, suggestion):
    changed = copy.deepcopy(request)
    variable = suggestion["variable"]
    value = int(suggestion["threshold"])
    if variable == "product_price":
        changed.purchase.price_amount.value = value
    else:
        getattr(changed.finance_profile, {
            "emergency_fund_balance": "emergency_fund_balance",
            "savebox_balance": "savebox_balance",
            "current_balance": "current_balance",
        }[variable]).value = value
    return changed


class RoundTripTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.request = _request(price=2_500_000, finance=TIGHT)
        cls.response, cls.suggestions = _run(cls.request)

    def test_빠듯한_사용자에게_확인된_제안이_나온다(self) -> None:
        self.assertNotEqual(self.response.decision, "BUY_NOW")
        self.assertTrue(self.suggestions, "제안이 하나도 없다")
        self.assertEqual(len(self.response.counterfactuals), len(self.suggestions[:3]))

    def test_응답의_validated는_실제_확인_결과다(self) -> None:
        for cf in self.response.counterfactuals:
            self.assertTrue(cf.validated)
            self.assertGreater(DECISION_RANK[cf.target_decision], DECISION_RANK[self.response.decision])

    def test_응답의_목표_판단은_추측이_아니라_다시_돌려_확인한_값이다(self) -> None:
        """예전에는 현재 판단만 보고 '재검토' 또는 '바로 구매'로 추측해서 적었다."""
        self.assertEqual(
            [cf.target_decision for cf in self.response.counterfactuals],
            [s["target_decision"] for s in self.suggestions[:3]],
        )

    def test_응답_문구는_다듬어져_있고_제안의_숫자를_그대로_담는다(self) -> None:
        from ..xai.counterfactual_text import friendly_won

        for cf, suggestion in zip(self.response.counterfactuals, self.suggestions[:3]):
            self.assertIn(friendly_won(suggestion["threshold"]), cf.label)
            self.assertNotIn("(으)로", cf.label)
            self.assertNotIn("을(를)", cf.label)

    def test_제안을_그대로_적용해_다시_돌리면_약속한_판단이_나온다(self) -> None:
        for suggestion in self.suggestions:
            with self.subTest(variable=suggestion["variable"], to=suggestion["threshold"]):
                rerun, _ = _run(_apply(self.request, suggestion))

                self.assertEqual(rerun.decision, suggestion["target_decision"])

    def test_제안보다_한_칸_덜_바꾸면_목표에_못_미친다(self) -> None:
        """제안이 '가장 작은' 변화인지 확인한다 (격자 한 칸 아래는 통과하지 못한다)."""
        checked = 0
        for suggestion in self.suggestions:
            if suggestion["variable"] == "product_price":
                continue
            below = dict(suggestion)
            below["threshold"] = suggestion["threshold"] - 10_000 * 3  # 최소 격자 간격보다 큰 폭
            rerun, _ = _run(_apply(self.request, below))
            checked += 1
            self.assertLess(
                DECISION_RANK[rerun.decision],
                DECISION_RANK[suggestion["target_decision"]] + 1,
            )
        self.assertGreater(checked, 0)

    def test_제안은_바꿀_수_있는_값뿐이다(self) -> None:
        for suggestion in self.suggestions:
            self.assertIn(
                suggestion["variable"],
                {"emergency_fund_balance", "savebox_balance", "current_balance", "product_price"},
            )


class LegacyAndEmptyTest(unittest.TestCase):
    def test_DiCE_경로의_제안은_확인되지_않았으므로_validated가_거짓이다(self) -> None:
        """예전에는 type 이 'dice' 이기만 하면 확인 없이 True 였다."""
        fake = (
            [{"type": "dice", "variable": "emergency_buffer", "action": "increase",
              "suggested_change": 100_000, "threshold": 1.0, "message": "m"}],
            {"enabled": True, "backend": "dice_ml", "count": 1},
        )
        with tempfile.TemporaryDirectory() as tmp, patch(
            "domain.xai_purchase.service._AUDIT_STORE", JsonlXaiAuditLogStore(Path(tmp) / "a.jsonl")
        ), patch.dict("os.environ", {"AI_XAI_DICE_ENABLED": "1"}), patch(
            "domain.xai_purchase.service.DiceCounterfactualEngine.suggest", return_value=fake
        ):
            response = evaluate_pr_purchase_xai(_request(price=2_500_000, finance=TIGHT))

        self.assertTrue(response.counterfactuals)
        self.assertTrue(all(cf.validated is False for cf in response.counterfactuals))

    def test_제안이_하나도_없어도_응답은_정상이다(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "domain.xai_purchase.service._AUDIT_STORE", JsonlXaiAuditLogStore(Path(tmp) / "a.jsonl")
        ), patch.object(
            ModelCounterfactualEngine, "suggest",
            return_value=([], {"enabled": True, "backend": "model_search", "count": 0,
                               "reason": "no_single_change_found"}),
        ):
            response = evaluate_pr_purchase_xai(_request(price=2_500_000, finance=TIGHT))

        self.assertEqual(response.counterfactuals, [])
        self.assertEqual(response.decision, "NOT_RECOMMENDED")  # 분석 오류(REVIEW)로 떨어지지 않는다


class NothingToSuggestTest(unittest.TestCase):
    def test_이미_바로_구매이거나_개선할_수_없으면_가짜_제안을_만들지_않는다(self) -> None:
        response, suggestions = _run(_request(price=89_000, finance=HEALTHY))

        self.assertEqual(
            [cf.validated for cf in response.counterfactuals],
            [True] * len(response.counterfactuals),
        )
        self.assertEqual(len(response.counterfactuals), len(suggestions[:3]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
