"""통합 가격 파서 테스트.

예전에는 가격 파서가 두 곳(xai/features.py, price_engine/normalizer.py)에 복사돼 있었고,
둘 다 문자열 속 모든 숫자를 이어 붙였다:
    "5% 할인 21,200원"      -> 521200
    "10,000원 ~ 12,000원"   -> 1000012000
    "$12.99"                -> 1299
    "2개 39,000원"          -> 239000
    "21만원"                -> 21
틀린 값이 조용히 가격 모델 학습 데이터와 실시간 판단에 들어갔다.
이제 읽을 수 없으면 값을 만들지 않고 이유를 상태로 남긴다.
"""

from __future__ import annotations

import unittest

from ..crawler.price import MAX_PRICE_KRW, PriceStatus, parse_price_krw


class ParsedTest(unittest.TestCase):
    def test_흔한_표기는_예전과_같은_값이다(self) -> None:
        """예전 파서가 맞게 읽던 입력은 그대로 읽어야 한다 (회귀 방지)."""
        for text, expected in [
            ("￦ 1,000 (KRW)", 1000),
            ("₩21,200", 21200),
            ("21,200", 21200),
            ("21,200원", 21200),
            ("21200", 21200),
            ("  39,000 원 ", 39000),
            ("KRW 15,000", 15000),
        ]:
            with self.subTest(text=text):
                result = parse_price_krw(text)
                self.assertEqual(result.status, PriceStatus.PARSED)
                self.assertEqual(result.amount, expected)

    def test_만_천_단위를_읽는다(self) -> None:
        for text, expected in [("21만원", 210_000), ("1.5만원", 15_000), ("3천원", 3_000), ("2만 5천원", 25_000)]:
            with self.subTest(text=text):
                self.assertEqual(parse_price_krw(text).amount, expected)

    def test_퍼센트와_수량은_가격이_아니다(self) -> None:
        for text, expected in [
            ("5% 할인 21,200원", 21_200),
            ("2개 39,000원", 39_000),
            ("39,000원 (2개)", 39_000),
            ("30% 21,000원", 21_000),
        ]:
            with self.subTest(text=text):
                result = parse_price_krw(text)
                self.assertEqual(result.status, PriceStatus.PARSED)
                self.assertEqual(result.amount, expected)

    def test_원_표시가_없어도_퍼센트와_수량은_걸러낸다(self) -> None:
        """'원' 이 붙은 금액이 있으면 그쪽을 우선하므로, 필터는 표시가 없을 때만 드러난다."""
        for text, expected in [("5% 할인 21,200", 21_200), ("2개 39,000", 39_000), ("3일 이내 15,000", 15_000)]:
            with self.subTest(text=text):
                result = parse_price_krw(text)
                self.assertEqual(result.status, PriceStatus.PARSED)
                self.assertEqual(result.amount, expected)

    def test_전각_문자도_읽는다(self) -> None:
        """사이트가 전각 ￦, 전각 숫자, 전각 쉼표를 쓴다 (￦ 는 실제 수집 데이터에 나온다)."""
        for text, expected in [("￦１２，０００", 12_000), ("￦1,000", 1_000), ("１２，０００원", 12_000)]:
            with self.subTest(text=text):
                self.assertEqual(parse_price_krw(text).amount, expected)

    def test_같은_금액이_반복되면_하나로_본다(self) -> None:
        self.assertEqual(parse_price_krw("21,200원 (₩21,200)").amount, 21_200)

    def test_원_표시가_붙은_금액이_우선한다(self) -> None:
        self.assertEqual(parse_price_krw("모델 1234 가격 21,200원").amount, 21_200)


class RejectedTest(unittest.TestCase):
    def test_범위는_모호하다(self) -> None:
        result = parse_price_krw("10,000원 ~ 12,000원")

        self.assertEqual(result.status, PriceStatus.AMBIGUOUS)
        self.assertIsNone(result.amount)

    def test_외화는_원화로_추측하지_않는다(self) -> None:
        for text in ["$12.99", "USD 30", "12.5 유로", "¥1,200", "€ 19,99"]:
            with self.subTest(text=text):
                result = parse_price_krw(text)
                self.assertEqual(result.status, PriceStatus.FOREIGN_CURRENCY)
                self.assertIsNone(result.amount)

    def test_통화_표시가_없는_소수는_모호하다(self) -> None:
        result = parse_price_krw("12.99")

        self.assertEqual(result.status, PriceStatus.AMBIGUOUS)
        self.assertIsNone(result.amount)

    def test_숫자가_없으면_이유를_남긴다(self) -> None:
        result = parse_price_krw("가격 미정")

        self.assertEqual(result.status, PriceStatus.NO_NUMBER)
        self.assertIsNone(result.amount)

    def test_없음과_빈_문자열은_누락이다(self) -> None:
        for value in (None, "", "   "):
            with self.subTest(value=value):
                self.assertEqual(parse_price_krw(value).status, PriceStatus.MISSING)  # type: ignore[arg-type]

    def test_문자열이_아니면_누락이다(self) -> None:
        self.assertEqual(parse_price_krw(12345).status, PriceStatus.MISSING)  # type: ignore[arg-type]

    def test_터무니없이_큰_값은_거부한다(self) -> None:
        result = parse_price_krw(f"{MAX_PRICE_KRW + 1:,}원")

        self.assertEqual(result.status, PriceStatus.OUT_OF_RANGE)
        self.assertIsNone(result.amount)

    def test_상한_이하는_통과한다(self) -> None:
        self.assertEqual(parse_price_krw(f"{MAX_PRICE_KRW:,}원").amount, MAX_PRICE_KRW)


class FreeTest(unittest.TestCase):
    def test_무료는_0원이다(self) -> None:
        for text in ("무료", "무료배송", "0원"):
            with self.subTest(text=text):
                result = parse_price_krw(text)
                self.assertEqual(result.status, PriceStatus.FREE)
                self.assertEqual(result.amount, 0)

    def test_무료와_금액이_같이_있으면_금액을_읽는다(self) -> None:
        result = parse_price_krw("무료배송 21,200원")

        self.assertEqual(result.status, PriceStatus.PARSED)
        self.assertEqual(result.amount, 21_200)


class ResultShapeTest(unittest.TestCase):
    def test_원문과_이유가_남는다(self) -> None:
        result = parse_price_krw("10,000원 ~ 12,000원")

        self.assertEqual(result.raw, "10,000원 ~ 12,000원")
        self.assertTrue(result.detail)

    def test_금액이_있을_때만_ok다(self) -> None:
        self.assertTrue(parse_price_krw("1,000원").ok)
        self.assertTrue(parse_price_krw("무료").ok)
        self.assertFalse(parse_price_krw("$1").ok)
        self.assertFalse(parse_price_krw(None).ok)  # type: ignore[arg-type]


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
