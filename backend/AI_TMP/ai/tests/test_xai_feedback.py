"""사용자 반응(좋았다/별로였다) 수집 계약."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient
from pydantic import ValidationError

from domain.xai_feedback.schemas import (
    MAX_COMMENT_LENGTH,
    MAX_REASONS,
    FeedbackStatus,
    PurchaseFeedbackRequest,
)
from domain.xai_feedback.service import EvaluationNotFound, PurchaseRequestMismatch, submit_feedback
from domain.xai_feedback.store import JsonlFeedbackStore
from domain.xai_purchase.audit_store import JsonlXaiAuditLogStore
from domain.xai_purchase.snapshot_store import SNAPSHOT_FINANCE_FIELDS, JsonlXaiSnapshotStore

from .test_budget_integration import WITH_INCOME
from .test_budget_integration import request as eval_request


def body(**override):
    data = {"purchaseRequestId": 7, "aspect": "price", "verdict": "good"}
    data.update(override)
    return PurchaseFeedbackRequest.model_validate(data)


def audit_with(path: Path, *pairs: tuple[str, int]) -> JsonlXaiAuditLogStore:
    store = JsonlXaiAuditLogStore(path)
    for request_id, purchase_id in pairs:
        store.save(request_id=request_id, purchase_request_id=purchase_id, warnings=[], runtime_engines={}, audit_logs=[{}])
    return store


class SchemaTest(unittest.TestCase):
    def test_허용되지_않는_값은_거부한다(self) -> None:
        for bad in ({"verdict": "meh"}, {"aspect": "weather"}, {"action": "maybe"}, {"reasons": ["NOPE"]}, {"extra": 1},
                    {"purchaseRequestId": -1}):
            with self.assertRaises(ValidationError, msg=bad):
                body(**bad)

    def test_필수값이_없으면_거부한다(self) -> None:
        for missing in ("purchaseRequestId", "aspect", "verdict"):
            data = {"purchaseRequestId": 7, "aspect": "price", "verdict": "good"}
            del data[missing]
            with self.assertRaises(ValidationError, msg=missing):
                PurchaseFeedbackRequest.model_validate(data)

    def test_사유는_중복을_없애고_개수를_제한한다(self) -> None:
        self.assertEqual([r.value for r in body(reasons=["OTHER", "OTHER", "PRICE_FAIR"]).reasons], ["OTHER", "PRICE_FAIR"])
        too_many = ["PRICE_TOO_HIGH", "PRICE_FAIR", "CHEAPER_ELSEWHERE", "BUDGET_TOO_TIGHT", "TOO_CAUTIOUS", "TOO_PERMISSIVE"]
        self.assertGreater(len(too_many), MAX_REASONS)
        with self.assertRaises(ValidationError):
            body(reasons=too_many)

    def test_코멘트는_공백을_다듬고_길이를_제한한다(self) -> None:
        self.assertEqual(body(comment="  좋았어요  ").comment, "좋았어요")
        self.assertIsNone(body(comment="   ").comment)
        with self.assertRaises(ValidationError):
            body(comment="가" * (MAX_COMMENT_LENGTH + 1))
        self.assertEqual(len(body(comment="가" * MAX_COMMENT_LENGTH).comment), MAX_COMMENT_LENGTH)

    def test_구매_여부를_안_보내면_알_수_없음이다(self) -> None:
        self.assertEqual(body().action.value, "unknown")


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "fb.jsonl"
        self.addCleanup(self.dir.cleanup)

    def rows(self):
        return [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l]

    def test_처음_보내면_기록된다(self) -> None:
        stored = JsonlFeedbackStore(self.path).save("r1", body())

        self.assertEqual(stored.status, FeedbackStatus.RECORDED)
        row = self.rows()[0]
        self.assertEqual((row["requestId"], row["aspect"], row["verdict"], row["supersedes"]), ("r1", "price", "good", None))
        self.assertIn("receivedAt", row)

    def test_같은_내용을_다시_보내면_중복이고_다시_쓰지_않는다(self) -> None:
        store = JsonlFeedbackStore(self.path)
        first = store.save("r1", body())
        again = store.save("r1", body())

        self.assertEqual(again.status, FeedbackStatus.DUPLICATE)
        self.assertEqual(again.feedback_id, first.feedback_id)
        self.assertEqual(len(self.rows()), 1)

    def test_사유_순서가_달라도_같은_내용이다(self) -> None:
        store = JsonlFeedbackStore(self.path)
        store.save("r1", body(reasons=["OTHER", "PRICE_FAIR"]))

        self.assertEqual(store.save("r1", body(reasons=["PRICE_FAIR", "OTHER"])).status, FeedbackStatus.DUPLICATE)

    def test_의견을_바꾸면_지우지_않고_이어서_쓴다(self) -> None:
        store = JsonlFeedbackStore(self.path)
        first = store.save("r1", body(verdict="good"))
        changed = store.save("r1", body(verdict="bad"))

        self.assertEqual(changed.status, FeedbackStatus.CHANGED)
        rows = self.rows()
        self.assertEqual([r["verdict"] for r in rows], ["good", "bad"])
        self.assertEqual(rows[1]["supersedes"], first.feedback_id)
        self.assertEqual([r["verdict"] for r in store.current_rows()], ["bad"])

    def test_대상이_다르면_서로_독립이다(self) -> None:
        store = JsonlFeedbackStore(self.path)
        store.save("r1", body(aspect="price", verdict="good"))

        self.assertEqual(store.save("r1", body(aspect="decision", verdict="bad")).status, FeedbackStatus.RECORDED)
        self.assertEqual(store.save("r2", body(aspect="price", verdict="bad")).status, FeedbackStatus.RECORDED)
        self.assertEqual(len(store.current_rows()), 3)

    def test_재시작해도_중복을_알아본다(self) -> None:
        JsonlFeedbackStore(self.path).save("r1", body())

        self.assertEqual(JsonlFeedbackStore(self.path).save("r1", body()).status, FeedbackStatus.DUPLICATE)
        self.assertEqual(len(self.rows()), 1)

    def test_깨진_줄이_있어도_나머지를_읽는다(self) -> None:
        JsonlFeedbackStore(self.path).save("r1", body())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write('{"requestId": "r9", "aspec\n')

        store = JsonlFeedbackStore(self.path)

        self.assertEqual([r["requestId"] for r in store.current_rows()], ["r1"])
        self.assertEqual(store.save("r1", body()).status, FeedbackStatus.DUPLICATE)

    def test_동시에_같은_반응이_와도_한_번만_기록된다(self) -> None:
        store = JsonlFeedbackStore(self.path)
        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(lambda _: store.save("r1", body()).status, range(48)))

        self.assertEqual(results.count(FeedbackStatus.RECORDED), 1)
        self.assertEqual(results.count(FeedbackStatus.DUPLICATE), 47)
        self.assertEqual(len(self.rows()), 1)


class AuditLookupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "audit.jsonl"
        self.addCleanup(self.dir.cleanup)

    def test_기록된_평가만_알아본다(self) -> None:
        store = audit_with(self.path, ("r1", 7), ("r2", 8))

        self.assertEqual(store.purchase_request_id_for("r1"), 7)
        self.assertEqual(store.purchase_request_id_for("r2"), 8)
        self.assertIsNone(store.purchase_request_id_for("nope"))

    def test_파일이_없으면_None(self) -> None:
        self.assertIsNone(JsonlXaiAuditLogStore(self.path).purchase_request_id_for("r1"))

    def test_나중에_추가된_평가도_알아본다(self) -> None:
        store = audit_with(self.path, ("r1", 7))
        self.assertIsNone(store.purchase_request_id_for("r2"))

        store.save(request_id="r2", purchase_request_id=8, warnings=[], runtime_engines={}, audit_logs=[{}])

        self.assertEqual(store.purchase_request_id_for("r2"), 8)
        self.assertEqual(store.purchase_request_id_for("r1"), 7)  # 앞서 읽은 것도 유지

    def test_쓰는_도중인_마지막_줄은_개행이_올_때까지_읽지_않는다(self) -> None:
        store = audit_with(self.path, ("r1", 7))
        store.purchase_request_id_for("r1")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write('{"requestId": "r2", "purchaseRequestId": 8')  # 아직 안 끝난 줄

        self.assertIsNone(store.purchase_request_id_for("r2"))

        with self.path.open("a", encoding="utf-8") as handle:
            handle.write("}\n")

        self.assertEqual(store.purchase_request_id_for("r2"), 8)

    def test_파일이_교체되면_색인을_다시_만든다(self) -> None:
        store = audit_with(self.path, ("r1", 7), ("r2", 8))
        store.purchase_request_id_for("r2")
        self.path.write_text(json.dumps({"requestId": "r3", "purchaseRequestId": 9}) + "\n", encoding="utf-8")

        self.assertEqual(store.purchase_request_id_for("r3"), 9)
        self.assertIsNone(store.purchase_request_id_for("r1"))

    def test_형식이_틀린_줄은_건너뛴다(self) -> None:
        store = audit_with(self.path)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write("123\n[1]\nnot json\n")
            handle.write(json.dumps({"requestId": "r1", "purchaseRequestId": True}) + "\n")  # bool 은 번호가 아니다
            handle.write(json.dumps({"requestId": "r2", "purchaseRequestId": 5}) + "\n")

        self.assertIsNone(store.purchase_request_id_for("r1"))
        self.assertEqual(store.purchase_request_id_for("r2"), 5)


class ServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.audit = audit_with(Path(self.dir.name) / "a.jsonl", ("r1", 7))
        self.store = JsonlFeedbackStore(Path(self.dir.name) / "f.jsonl")

    def test_모르는_평가는_거부한다(self) -> None:
        with self.assertRaises(EvaluationNotFound):
            submit_feedback("zzz", body(), evaluations=self.audit, store=self.store)
        self.assertEqual(self.store.current_rows(), [])

    def test_구매_요청_번호가_다르면_거부한다(self) -> None:
        with self.assertRaises(PurchaseRequestMismatch) as ctx:
            submit_feedback("r1", body(purchaseRequestId=99), evaluations=self.audit, store=self.store)
        self.assertEqual((ctx.exception.expected, ctx.exception.got), (7, 99))
        self.assertEqual(self.store.current_rows(), [])

    def test_정상이면_기록하고_응답한다(self) -> None:
        response = submit_feedback("r1", body(), evaluations=self.audit, store=self.store)

        self.assertEqual((response.request_id, response.status), ("r1", FeedbackStatus.RECORDED))
        self.assertEqual(len(self.store.current_rows()), 1)


class ApiTest(unittest.TestCase):
    def setUp(self) -> None:
        from main import app

        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        audit = audit_with(Path(self.dir.name) / "a.jsonl", ("req-1", 7))
        store = JsonlFeedbackStore(Path(self.dir.name) / "f.jsonl")
        for target, value in (("domain.xai_purchase.service._AUDIT_STORE", audit), ("api.v1.routers.xai_feedback._STORE", store)):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(app)
        self.url = "/api/v1/xai/purchase-evaluations/req-1/feedback"
        self.payload = {"purchaseRequestId": 7, "aspect": "price", "verdict": "good", "reasons": ["PRICE_FAIR"]}

    def test_엔드포인트가_문서에_있다(self) -> None:
        from main import app

        self.assertIn("/api/v1/xai/purchase-evaluations/{request_id}/feedback", app.openapi()["paths"])

    def test_기록되면_200과_camelCase_응답(self) -> None:
        res = self.client.post(self.url, json=self.payload)

        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(
            (data["requestId"], data["purchaseRequestId"], data["aspect"], data["verdict"], data["status"]),
            ("req-1", 7, "price", "good", "recorded"),
        )
        self.assertTrue(data["feedbackId"].startswith("fb_"))

    def test_재전송은_duplicate_바꾸면_changed(self) -> None:
        self.client.post(self.url, json=self.payload)

        self.assertEqual(self.client.post(self.url, json=self.payload).json()["status"], "duplicate")
        self.assertEqual(self.client.post(self.url, json={**self.payload, "verdict": "bad"}).json()["status"], "changed")

    def test_모르는_평가는_404(self) -> None:
        res = self.client.post("/api/v1/xai/purchase-evaluations/nope/feedback", json=self.payload)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["detail"]["code"], "EVALUATION_NOT_FOUND")

    def test_구매_요청_번호가_다르면_422(self) -> None:
        res = self.client.post(self.url, json={**self.payload, "purchaseRequestId": 8})

        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["detail"]["code"], "PURCHASE_REQUEST_MISMATCH")
        self.assertEqual(res.json()["detail"]["expectedPurchaseRequestId"], 7)

    def test_잘못된_본문은_422(self) -> None:
        for bad in ({**self.payload, "verdict": "great"}, {**self.payload, "unknown": 1}, {"aspect": "price"}):
            self.assertEqual(self.client.post(self.url, json=bad).status_code, 422, bad)


class EndToEndTest(unittest.TestCase):
    """실제 평가를 하고 그 requestId 로 반응을 보내는 흐름, 그리고 입력 스냅샷."""

    def setUp(self) -> None:
        from main import app

        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        root = Path(self.dir.name)
        self.snapshot_path = root / "snap.jsonl"
        for target, value in (
            ("domain.xai_purchase.service._AUDIT_STORE", JsonlXaiAuditLogStore(root / "a.jsonl")),
            ("domain.xai_purchase.service._SNAPSHOT_STORE", JsonlXaiSnapshotStore(self.snapshot_path)),
            ("api.v1.routers.xai_feedback._STORE", JsonlFeedbackStore(root / "f.jsonl")),
        ):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(app)

    def _evaluate(self, **kw):
        from domain.xai_purchase.service import evaluate_pr_purchase_xai

        return evaluate_pr_purchase_xai(eval_request(300_000, WITH_INCOME), **kw)

    def test_평가한_requestId_로_반응을_보낼_수_있다(self) -> None:
        response = self._evaluate()

        res = self.client.post(
            f"/api/v1/xai/purchase-evaluations/{response.request_id}/feedback",
            json={"purchaseRequestId": response.purchase_request_id, "aspect": "decision", "verdict": "good"},
        )

        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["status"], "recorded")

    def test_랩의_모의_평가는_기록되지_않아_반응을_받지_않는다(self) -> None:
        response = self._evaluate(record_audit=False)

        res = self.client.post(
            f"/api/v1/xai/purchase-evaluations/{response.request_id}/feedback",
            json={"purchaseRequestId": response.purchase_request_id, "aspect": "decision", "verdict": "good"},
        )

        self.assertEqual(res.status_code, 404)

    def test_스냅샷은_기본으로_저장하지_않는다(self) -> None:
        import os

        with patch.dict("os.environ"):
            os.environ.pop("AI_XAI_SNAPSHOT_ENABLED", None)  # 설정 자체가 없을 때의 기본값
            self._evaluate()

        self.assertFalse(self.snapshot_path.exists() and self.snapshot_path.read_text().strip())

    def test_저장소는_허용된_재무_필드만_받는다(self) -> None:
        store = JsonlXaiSnapshotStore(self.snapshot_path)
        store.save(
            request_id="r1", purchase_request_id=1, decision="WAIT", price=1000.0,
            finance_profile={"current_balance": 5, "item_title": "비밀 상품명", "merchant": "비밀 가맹점"},
            origins={"current_balance": "upstream", "merchant": "upstream"},
            budget=None, rule_version=None, model_version=None,
        )

        text = self.snapshot_path.read_text(encoding="utf-8")
        row = json.loads(text)
        self.assertEqual(row["financeProfile"], {"current_balance": 5})
        self.assertEqual(row["origins"], {"current_balance": "upstream"})
        self.assertNotIn("비밀", text)

    def test_켜면_숫자와_판단만_저장하고_식별_문자열은_저장하지_않는다(self) -> None:
        with patch.dict("os.environ", {"AI_XAI_SNAPSHOT_ENABLED": "1"}):
            response = self._evaluate()

        rows = [json.loads(line) for line in self.snapshot_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(set(row), {"requestId", "purchaseRequestId", "loggedAt", "decision", "price", "financeProfile",
                                    "origins", "budget", "ruleVersion", "modelVersion"})
        self.assertEqual((row["requestId"], row["decision"], row["price"]), (response.request_id, response.decision, 300_000))
        self.assertEqual(row["financeProfile"]["available_fixed_income"], 3_000_000)
        self.assertEqual(row["financeProfile"]["monthly_spending_30d"], 400_000)
        self.assertLessEqual(set(row["financeProfile"]), set(SNAPSHOT_FINANCE_FIELDS))
        self.assertEqual(row["origins"]["available_fixed_income"], "upstream")
        self.assertEqual(row["budget"]["status"], "over")

    def test_랩_모의_평가는_스냅샷도_남기지_않는다(self) -> None:
        with patch.dict("os.environ", {"AI_XAI_SNAPSHOT_ENABLED": "1"}):
            self._evaluate(record_audit=False)

        self.assertFalse(self.snapshot_path.exists() and self.snapshot_path.read_text().strip())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
