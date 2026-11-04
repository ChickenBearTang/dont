"""반사실 문구 다듬기 테스트.

예전 문구: "비상자금을(를) 약 1,110,000원 늘려 1,280,000원이 되면 구매 판단이 '대기'(으)로 바뀝니다."
 - 금액이 자릿수를 세어야 읽힌다
 - 지금 판단에서 어디로 바뀌는지가 없다
 - 목표를 이뤄도 남는 걸림돌(카드 결제일 등)을 말하지 않는다
 - 그 금액이 내 월 지출에 비해 큰지 작은지 감이 안 온다
숫자는 절대 바뀌면 안 된다. 보기 좋게 다듬되 제안의 사실은 그대로 보존해야 한다.
"""

from __future__ import annotations

import re
import unittest

from ..xai.counterfactual_text import (
    DECISION_LABEL_KO,
    friendly_won,
    polish_counterfactuals,
    render_counterfactual,
)

CTX = dict(current_decision="NOT_RECOMMENDED", monthly_spending=1_300_000.0, days_until_card_due=2, price=2_500_000.0)


def _s(variable="emergency_fund_balance", delta=1_110_000, threshold=1_260_000.0, target="WAIT", action="increase"):
    return {"variable": variable, "action": action, "suggested_change": delta, "threshold": threshold,
            "target_decision": target, "validated": True, "type": "model_search", "relative_cost": delta / 1_300_000}


def _parse_won(text: str) -> int:
    """'4만 9천 원', '1억 2,000만 원' 같은 표기를 숫자로 되돌린다 (테스트용)."""
    total = 0
    for number, unit in re.findall(r"([\d,]+)\s*(억|만|천|백)", text):
        n = int(number.replace(",", ""))
        total += n * {"억": 100_000_000, "만": 10_000, "천": 1_000, "백": 100}[unit]
    tail = re.search(r"(\d[\d,]*)\s*원", text)
    if tail and not re.search(r"(억|만|천|백)\s*원", text):
        total += int(tail.group(1).replace(",", ""))
    return total


class FriendlyWonTest(unittest.TestCase):
    def test_읽기_쉬운_한국어_금액(self) -> None:
        for amount, expected in [
            (1_110_000, "111만 원"),
            (49_000, "4만 9천 원"),
            (8_500, "8천 5백 원"),
            (120_000_000, "1억 2,000만 원"),
            (2_500_000, "250만 원"),
            (999, "999원"),
            (0, "0원"),
        ]:
            with self.subTest(amount=amount):
                self.assertEqual(friendly_won(amount), expected)

    def test_반올림되면_약을_붙인다(self) -> None:
        self.assertEqual(friendly_won(1_284_500), "약 128만 원")
        self.assertEqual(friendly_won(49_300), "약 4만 9천 원")

    def test_정확히_떨어지면_약을_붙이지_않는다(self) -> None:
        self.assertFalse(friendly_won(1_110_000).startswith("약"))

    def test_숫자가_바뀌지_않는다(self) -> None:
        """사람이 읽기 좋게 줄이되, 원래 값에서 반올림 단위 이상 벗어나면 안 된다."""
        for amount in (7_300, 49_000, 123_456, 1_110_000, 12_345_678, 250_000_000):
            with self.subTest(amount=amount):
                parsed = _parse_won(friendly_won(amount))
                unit = 10_000 if amount >= 100_000 else 1_000 if amount >= 10_000 else 100
                self.assertLessEqual(abs(parsed - amount), unit / 2 + 1)

    def test_음수와_비정상은_0으로_본다(self) -> None:
        self.assertEqual(friendly_won(-5), "0원")
        self.assertEqual(friendly_won(float("nan")), "0원")


class RenderTest(unittest.TestCase):
    def test_금액과_판단_변화가_모두_들어간다(self) -> None:
        text = render_counterfactual(_s(), **CTX)

        self.assertIn("111만 원", text)
        self.assertIn("126만 원", text)
        self.assertIn(DECISION_LABEL_KO["NOT_RECOMMENDED"], text)
        self.assertIn(DECISION_LABEL_KO["WAIT"], text)

    def test_기계적인_예전_문구가_아니다(self) -> None:
        text = render_counterfactual(_s(), **CTX)

        self.assertNotIn("(으)로", text)
        self.assertNotIn("을(를)", text)
        self.assertNotIn("1,110,000", text)

    def test_조사가_받침에_맞다(self) -> None:
        """'관망'(받침 있음)은 '으로', '바로 구매'/'추가 검토'(받침 없음)는 '로'."""
        for target, current, expected in [
            ("WAIT", "NOT_RECOMMENDED", "'관망'으로"),
            ("BUY_NOW", "REVIEW", "'바로 구매'로"),
            ("REVIEW", "WAIT", "'추가 검토'로"),
            ("NOT_RECOMMENDED", "BUY_NOW", "'구매 비추천'으로"),
        ]:
            with self.subTest(target=target):
                text = render_counterfactual(_s(target=target), **{**CTX, "current_decision": current})
                self.assertIn(expected, text)

    def test_월_지출_대비_규모를_말한다(self) -> None:
        text = render_counterfactual(_s(delta=1_110_000), **CTX)

        self.assertIn("월 지출의 약 85%", text)  # 1,110,000 / 1,300,000

    def test_가격_제안은_할인율을_말한다(self) -> None:
        text = render_counterfactual(
            _s(variable="product_price", action="decrease", delta=1_250_000, threshold=1_250_000.0), **CTX
        )

        self.assertIn("125만 원", text)
        self.assertIn("50%", text)  # 2,500,000 -> 1,250,000
        self.assertIn("내려", text)

    def test_변수마다_다른_말을_쓴다(self) -> None:
        texts = {v: render_counterfactual(_s(variable=v), **CTX)
                 for v in ("emergency_fund_balance", "savebox_balance", "current_balance")}

        self.assertIn("비상자금", texts["emergency_fund_balance"])
        self.assertIn("세이브박스", texts["savebox_balance"])
        self.assertIn("계좌 잔액", texts["current_balance"])

    def test_대기로_바뀌고_결제일이_임박하면_결제일_뒤를_권한다(self) -> None:
        text = render_counterfactual(_s(target="WAIT"), **{**CTX, "days_until_card_due": 2})

        self.assertIn("카드 결제일이 2일", text)
        self.assertIn("다시", text)

    def test_결제일이_멀면_결제일_이야기를_하지_않는다(self) -> None:
        text = render_counterfactual(_s(target="WAIT"), **{**CTX, "days_until_card_due": 20})

        self.assertNotIn("결제일", text)

    def test_바로_구매로_바뀌면_추가_조건을_붙이지_않는다(self) -> None:
        text = render_counterfactual(_s(target="BUY_NOW"), **{**CTX, "current_decision": "REVIEW"})

        self.assertIn(DECISION_LABEL_KO["BUY_NOW"], text)
        self.assertNotIn("결제일", text)

    def test_목표_금액이_월_지출의_2배를_넘으면_부담을_솔직히_말한다(self) -> None:
        text = render_counterfactual(_s(delta=3_000_000, threshold=3_150_000.0), **CTX)

        self.assertIn("단기간", text)

    def test_알_수_없는_변수는_일반_문장으로_폴백한다(self) -> None:
        text = render_counterfactual(_s(variable="mystery"), **CTX)

        self.assertTrue(text)
        self.assertIn("111만 원", text)

    def test_월_지출이_0이어도_깨지지_않는다(self) -> None:
        text = render_counterfactual(_s(), **{**CTX, "monthly_spending": 0.0})

        self.assertTrue(text)

    def test_변경량이_0이면_수치를_말하지_않는다(self) -> None:
        text = render_counterfactual(_s(delta=0, threshold=100.0), **CTX)

        self.assertNotIn("0원", text)


class PolishAllTest(unittest.TestCase):
    def test_구조화_필드는_그대로_두고_message만_바꾼다(self) -> None:
        original = [_s(), _s(variable="savebox_balance", delta=2_000_000, threshold=2_150_000.0)]
        before = [dict(o) for o in original]

        out = polish_counterfactuals(original, **CTX)

        self.assertEqual(original, before)  # 입력을 바꾸지 않는다
        for new, old in zip(out, before):
            self.assertEqual({k: v for k, v in new.items() if k != "message"},
                             {k: v for k, v in old.items() if k != "message"})
            self.assertTrue(new["message"])

    def test_확인되지_않은_제안의_문구는_건드리지_않는다(self) -> None:
        """validated 가 아닌(DiCE 등) 제안은 새 사실을 말하면 안 되므로 원문 그대로 둔다."""
        legacy = {"type": "dice", "variable": "emergency_buffer", "action": "increase",
                  "suggested_change": 100_000, "threshold": 1.0, "message": "원문"}

        out = polish_counterfactuals([legacy], **CTX)

        self.assertEqual(out[0]["message"], "원문")


class SummaryPolisherTest(unittest.TestCase):
    def _polish(self, decision, reason="비상자금 수준이 낮아 재무 안정성이 부족합니다.", suggestion="비상자금을 222만 원 더 늘리면 나아집니다."):
        from ..xai.polisher import LLMSummaryPolisher

        return LLMSummaryPolisher().polish(decision=decision, top_reason_text=reason, suggestion_text=suggestion)

    def test_예전의_이름표_나열이_아니다(self) -> None:
        text = self._polish("NOT_RECOMMENDED")

        self.assertNotIn("핵심 근거:", text)
        self.assertNotIn("개선 포인트:", text)

    def test_판단_근거_제안_순서의_자연스러운_문장이다(self) -> None:
        text = self._polish("NOT_RECOMMENDED")

        self.assertTrue(text.startswith("지금은 구매를 권하지 않습니다."))
        self.assertLess(text.index("재무 안정성"), text.index("222만 원"))

    def test_판단마다_다른_첫_문장이다(self) -> None:
        leads = {d: self._polish(d).split(".")[0] for d in ("BUY_NOW", "WAIT", "NOT_RECOMMENDED", "REVIEW")}

        self.assertEqual(len(set(leads.values())), 4)

    def test_문장부호가_없는_입력에_마침표를_붙이고_중복하지_않는다(self) -> None:
        text = self._polish("WAIT", reason="가격이 높습니다", suggestion="재평가")

        self.assertIn("가격이 높습니다.", text)
        self.assertNotIn("..", text)

    def test_빈_입력은_건너뛴다(self) -> None:
        text = self._polish("BUY_NOW", reason="", suggestion="")

        self.assertEqual(text, "지금 구매해도 좋은 조건입니다.")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
