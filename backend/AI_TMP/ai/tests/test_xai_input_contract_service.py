"""입력 계약이 운영 경로(HTTP -> service -> analyzer)에 실제로 연결됐는지 검증한다.

test_xai_input_contract.py 가 계약 모듈 자체를 본다면, 여기서는 "계약이 있다"가
아니라 "운영 경로가 그 계약을 쓴다"를 본다. 모듈만 있고 연결이 빠지면 앞쪽
테스트는 통과하면서 사고는 그대로 재발하기 때문이다.
"""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# 서비스는 `domain.xai_purchase...` 이름으로 import 되므로 patch 대상과 같은
# 모듈 객체를 쓰려면 다른 서비스 테스트처럼 src 를 sys.path 에 넣어야 한다.
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient

from consumption_poc.main import app
from domain.xai_purchase.audit_store import JsonlXaiAuditLogStore
from domain.xai_purchase.service import _evidence_origin
from .test_pr_xai_endpoint import _payload

ENDPOINT = "/api/v1/xai/purchase-evaluations"

_OPTIONAL = ("saveboxBalance", "availableFixedExpense", "availableFixedIncome")


def _provenance(value: object, **flags: bool) -> dict[str, object]:
    return {
        "value": value,
        "source": "spring.finance_profile",
        "snapshotId": "fin-1",
        "isDefault": flags.get("is_default", False),
        "isEstimated": flags.get("is_estimated", False),
    }


def _payload_with_all_optional() -> dict[str, object]:
    payload = _payload()
    profile = payload["financeProfile"]
    assert isinstance(profile, dict)
    profile["saveboxBalance"] = _provenance(500_000)
    profile["availableFixedExpense"] = _provenance(400_000)
    profile["availableFixedIncome"] = _provenance(3_000_000)
    return payload


def _post(payload: dict[str, object]):
    # 서비스는 평가마다 감사 로그를 저장소의 추적 파일(data/xai_audit_log.jsonl)에
    # 이어 쓴다. 테스트가 그 파일을 더럽히지 않도록 임시 저장소로 바꿔 끼운다.
    with tempfile.TemporaryDirectory() as tmp_dir, patch(
        "domain.xai_purchase.service._AUDIT_STORE",
        JsonlXaiAuditLogStore(Path(tmp_dir) / "audit.jsonl"),
    ), patch(
        "domain.xai_purchase.service._fetch_page_text",
        return_value=(None, "MISSING_PURCHASE_URL"),
    ):
        return TestClient(app).post(ENDPOINT, json=payload)


class ContractViolationOverHttpTest(unittest.TestCase):
    def test_필수_필드_값이_null이면_422와_필드_단위_원인을_돌려준다(self) -> None:
        """pydantic 이 통과시키던 구멍. 예전에는 여기서 0.0 이 조용히 들어갔다."""
        payload = _payload_with_all_optional()
        payload["financeProfile"]["currentBalance"]["value"] = None  # type: ignore[index]

        response = _post(payload)

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail["code"], "XAI_INPUT_CONTRACT_VIOLATION")
        self.assertEqual(
            [(v["field"], v["code"]) for v in detail["violations"]],
            [("current_balance", "missing")],
        )

    def test_숫자가_아닌_값은_422다(self) -> None:
        payload = _payload_with_all_optional()
        payload["financeProfile"]["emergencyFundBalance"]["value"] = "많음"  # type: ignore[index]

        response = _post(payload)

        self.assertEqual(response.status_code, 422)
        violations = response.json()["detail"]["violations"]
        self.assertEqual(violations[0]["field"], "emergency_fund_balance")
        self.assertEqual(violations[0]["code"], "not_numeric")

    def test_여러_위반을_한_번에_보고한다(self) -> None:
        payload = _payload_with_all_optional()
        profile = payload["financeProfile"]
        profile["currentBalance"]["value"] = None  # type: ignore[index]
        profile["daysUntilCardDue"]["value"] = 10.5  # type: ignore[index]

        response = _post(payload)

        self.assertEqual(response.status_code, 422)
        fields = {v["field"] for v in response.json()["detail"]["violations"]}
        self.assertEqual(fields, {"current_balance", "days_until_card_due"})

    def test_깨진_선택_필드는_기본값으로_덮지_않고_거부한다(self) -> None:
        payload = _payload_with_all_optional()
        payload["financeProfile"]["availableFixedIncome"]["value"] = "abc"  # type: ignore[index]

        response = _post(payload)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["detail"]["violations"][0]["field"],
            "available_fixed_income",
        )

    def test_0원_잔고는_정당한_입력이다(self) -> None:
        payload = _payload_with_all_optional()
        payload["financeProfile"]["currentBalance"]["value"] = 0  # type: ignore[index]

        response = _post(payload)

        self.assertEqual(response.status_code, 200)


class DefaultVisibilityTest(unittest.TestCase):
    """기본값으로 채워진 사실이 응답에서 보여야 한다."""

    def test_Spring이_보내지_않는_필드는_경고와_근거로_드러난다(self) -> None:
        """Spring 은 고정 수입/지출을 아예 보내지 않는다 (PrXaiFinanceProfileDto)."""
        response = _post(_payload())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        for name in (
            "available_fixed_income",
            "available_fixed_expense",
            "savebox_balance",
        ):
            self.assertIn(f"FINANCE_FIELD_DEFAULTED:{name}", body["warnings"], name)

        evidence = {e["field"]: e for e in body["supportingEvidence"]}
        income = evidence["available_fixed_income"]
        self.assertTrue(income["isDefault"])
        self.assertEqual(income["value"], "1000000.0")
        self.assertEqual(income["source"], "fastapi.input_contract")

    def test_모두_보내면_기본값_경고가_없다(self) -> None:
        response = _post(_payload_with_all_optional())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            [w for w in body["warnings"] if w.startswith("FINANCE_FIELD_")], []
        )
        self.assertFalse(
            any(e["source"] == "fastapi.input_contract" for e in body["supportingEvidence"])
        )

    def test_기본값이_많을수록_dataCompleteness가_내려간다(self) -> None:
        complete = _post(_payload_with_all_optional()).json()
        sparse = _post(_payload()).json()

        self.assertLess(
            sparse["confidence"]["dataCompleteness"],
            complete["confidence"]["dataCompleteness"],
        )

    def test_앞단이_isDefault를_true로_보내면_경고로_드러난다(self) -> None:
        """Spring 은 카드 없는 사용자의 결제일 14일을 isDefault=false 로 보낸다.
        그 버그를 고치면 이 경로로 가시화된다."""
        payload = _payload_with_all_optional()
        payload["financeProfile"]["daysUntilCardDue"] = _provenance(  # type: ignore[index]
            14, is_default=True
        )

        body = _post(payload).json()

        self.assertIn("FINANCE_FIELD_DEFAULTED:days_until_card_due", body["warnings"])

    def test_앞단이_isEstimated를_true로_보내면_경고로_드러난다(self) -> None:
        payload = _payload_with_all_optional()
        payload["financeProfile"]["saveboxBalance"] = _provenance(  # type: ignore[index]
            500_000, is_estimated=True
        )

        body = _post(payload).json()

        self.assertIn("FINANCE_FIELD_ESTIMATED:savebox_balance", body["warnings"])


class BehaviorPreservedTest(unittest.TestCase):
    """계약 연결이 판단 자체를 바꾸지 않았음을 고정한다.

    이 리팩토링의 목적은 '숨은 기본값을 드러내는 것'이지 '판단을 바꾸는 것'이
    아니다. 기본값으로 채운 경우와 같은 값을 명시적으로 보낸 경우는 결정과
    재무 평가가 같아야 한다.
    """

    def test_기본값으로_채운_것과_같은_값을_명시해도_결정은_같다(self) -> None:
        implicit = _payload()
        profile = implicit["financeProfile"]
        explicit = copy.deepcopy(implicit)
        emergency = profile["emergencyFundBalance"]["value"]  # type: ignore[index]
        explicit["financeProfile"]["saveboxBalance"] = _provenance(emergency)  # type: ignore[index]
        explicit["financeProfile"]["availableFixedExpense"] = _provenance(0)  # type: ignore[index]
        explicit["financeProfile"]["availableFixedIncome"] = _provenance(1_000_000)  # type: ignore[index]

        a = _post(implicit).json()
        b = _post(explicit).json()

        self.assertEqual(a["decision"], b["decision"])
        self.assertEqual(
            a["financialEvaluation"]["status"], b["financialEvaluation"]["status"]
        )
        self.assertEqual(
            a["financialEvaluation"]["keyMetrics"],
            b["financialEvaluation"]["keyMetrics"],
        )


class EvidenceOriginMappingTest(unittest.TestCase):
    def test_근거_feature가_재무_필드_출처로_연결된다(self) -> None:
        from ai.xai.input_contract import RawField, resolve_finance_profile

        profile = resolve_finance_profile(
            {
                "current_balance": RawField(1),
                "emergency_fund_balance": RawField(1),
                "expected_card_payment_amount": RawField(1),
                "days_until_card_due": RawField(14, is_default=True),
            }
        )

        self.assertEqual(_evidence_origin("days_until_card_due", profile), "default")
        self.assertEqual(_evidence_origin("projected_balance_after_purchase", profile), "default")
        self.assertEqual(_evidence_origin("emergency_fund_balance", profile), "upstream")
        self.assertIsNone(_evidence_origin("current_price", profile))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
