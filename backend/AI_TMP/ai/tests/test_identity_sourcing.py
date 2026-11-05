"""유통경로(정식수입/병행수입/직구/구매대행) 판정."""

from __future__ import annotations

import unittest

from ..crawler.identity.tables.models import ProductTables, SourcingCategoryRow, SourcingSignalRow
from ..crawler.identity.tables.sourcing import SourcingClassifier, host_of

CATS = [
    SourcingCategoryRow("OFFICIAL", "정식수입", "Y", "Y", "Y"),
    SourcingCategoryRow("PARALLEL", "병행수입", "U", "N"),
    SourcingCategoryRow("DIRECT", "해외직구", "N", "N"),
    SourcingCategoryRow("AGENCY", "구매대행", "U", "N"),
]


def classifier(*signals, categories=CATS):
    return SourcingClassifier(categories, signals)


def S(cat, kind, pattern, priority=100, enabled="Y"):
    return SourcingSignalRow(cat, kind, pattern, priority, enabled)


class HostTest(unittest.TestCase):
    def test_여러_모양의_주소에서_호스트를_뽑는다(self) -> None:
        cases = {
            "https://ko.AliExpress.com/item/1.html?x=1": "ko.aliexpress.com",
            "http://user:pw@shop.example.com:8080/a": "shop.example.com",
            "aliexpress.com/item/1": "aliexpress.com",
            "//amazon.com/dp/B0": "amazon.com",
            "https://example.com./": "example.com",
        }
        for url, host in cases.items():
            self.assertEqual(host_of(url), host, url)

    def test_주소가_아니거나_이상하면_None(self) -> None:
        for url in (None, "", "   ", "ftp://aliexpress.com/x", "javascript:void(0)", "mailto:a@b.com", "http://", "https://[::1"):
            self.assertIsNone(host_of(url), url)


class ClassifyTest(unittest.TestCase):
    def test_신호가_없으면_경로를_모른다고_하고_국내로_가정하지_않는다(self) -> None:
        result = classifier(S("DIRECT", "keyword", "직구")).classify("로지텍 마우스 109,000원")

        self.assertEqual((result.status, result.category_code, result.price_pool), ("none", None, None))

    def test_키워드는_공백과_기호를_무시하고_어디에든_들어_있으면_일치한다(self) -> None:
        c = classifier(S("DIRECT", "keyword", "직구"))

        for title in ("해외직구 마우스", "[직구] 마우스", "마우스 해외 직구", "직구템 마우스", "마우스(직-구)"):
            self.assertEqual(c.classify(title).category_code, "DIRECT", title)

    def test_여러_단어_키워드는_띄어쓰기와_상관없이_일치한다(self) -> None:
        c = classifier(S("OFFICIAL", "keyword", "정식 발매"))

        self.assertEqual(c.classify("정식발매 상품").category_code, "OFFICIAL")
        self.assertEqual(c.classify("정식   발매 상품").category_code, "OFFICIAL")
        self.assertEqual(c.classify("정식 상품 발매").status, "none")  # 사이에 다른 말이 끼면 아니다

    def test_토큰_신호는_토큰이_정확히_같을_때만_일치한다(self) -> None:
        c = classifier(S("DIRECT", "token", "ebay"))

        self.assertEqual(c.classify("[eBay] 마우스").category_code, "DIRECT")
        self.assertEqual(c.classify("ebay-마우스").category_code, "DIRECT")
        self.assertEqual(c.classify("freebay 마우스").status, "none")
        self.assertEqual(c.classify("ebays 마우스").status, "none")

    def test_토큰_신호는_여러_토큰이_이어서_나와야_한다(self) -> None:
        c = classifier(S("DIRECT", "token", "global rocket"))

        self.assertEqual(c.classify("global rocket 배송").category_code, "DIRECT")
        self.assertEqual(c.classify("global fast rocket").status, "none")

    def test_도메인은_호스트가_같거나_하위_도메인일_때만_일치한다(self) -> None:
        c = classifier(S("DIRECT", "domain", "aliexpress.com"))

        for url in ("https://aliexpress.com/item/1", "https://ko.aliexpress.com/item/1", "aliexpress.com/x"):
            self.assertEqual(c.classify("마우스", url).category_code, "DIRECT", url)
        for url in ("https://notaliexpress.com/x", "https://aliexpress.com.evil.net/x", "https://evil.net/aliexpress.com", None):
            self.assertEqual(c.classify("마우스", url).status, "none", url)

    def test_꺼진_신호와_없는_경로의_신호는_쓰지_않는다(self) -> None:
        c = classifier(S("DIRECT", "keyword", "직구", enabled="N"), S("GHOST", "keyword", "유령"))

        self.assertEqual(c.classify("직구 유령").status, "none")
        self.assertEqual(len(c), 0)

    def test_분류되면_경로의_규칙_값이_따라온다(self) -> None:
        direct = classifier(S("DIRECT", "keyword", "직구")).classify("직구 마우스")
        official = classifier(S("OFFICIAL", "keyword", "정발")).classify("정발 마우스")

        self.assertEqual((direct.kc_record_expected, direct.price_pool, direct.reviewed, direct.label_ko), ("N", False, False, "해외직구"))
        self.assertEqual((official.kc_record_expected, official.price_pool, official.reviewed), ("Y", True, True))

    def test_가장_작은_priority_의_신호만_판정한다(self) -> None:
        c = classifier(S("DIRECT", "domain", "amazon.com", 10), S("OFFICIAL", "keyword", "정발", 50))

        result = c.classify("정발 마우스", "https://amazon.com/dp/1")

        self.assertEqual((result.status, result.category_code), ("classified", "DIRECT"))
        self.assertEqual(len(result.evidence), 1)

    def test_같은_priority_에서_서로_다른_경로면_충돌로_알리고_고르지_않는다(self) -> None:
        c = classifier(S("PARALLEL", "keyword", "병행", 50), S("DIRECT", "keyword", "직구", 50))

        result = c.classify("병행 직구 마우스")

        self.assertEqual((result.status, result.category_code, result.price_pool), ("conflict", None, None))
        self.assertEqual(result.conflicting, ("DIRECT", "PARALLEL"))
        self.assertEqual(len(result.evidence), 2)

    def test_같은_경로를_가리키는_여러_신호는_충돌이_아니다(self) -> None:
        c = classifier(S("DIRECT", "keyword", "직구", 50), S("DIRECT", "keyword", "아마존", 50), S("DIRECT", "domain", "amazon.com", 50))

        result = c.classify("아마존 직구 마우스", "https://amazon.com/x")

        self.assertEqual((result.status, result.category_code), ("classified", "DIRECT"))
        self.assertEqual(len(result.evidence), 3)

    def test_더_구체적인_신호가_먼저_이긴다(self) -> None:
        c = classifier(S("AGENCY", "keyword", "구매대행", 40), S("DIRECT", "keyword", "직구", 50))

        self.assertEqual(c.classify("해외직구 구매대행 마우스").category_code, "AGENCY")

    def test_빈_제목과_None_도_다룬다(self) -> None:
        c = classifier(S("DIRECT", "keyword", "직구"))

        self.assertEqual(c.classify("").status, "none")
        self.assertEqual(c.classify(None).status, "none")  # type: ignore[arg-type]


class FromTablesTest(unittest.TestCase):
    def test_검증을_통과한_행만_쓰고_걸러진_행은_알린다(self) -> None:
        tables = ProductTables(
            categories=CATS,
            signals=[S("DIRECT", "keyword", "직구"), S("DIRECT", "domain", "https://bad.com/x"), S("DIRECT", "keyword", "정발"), S("OFFICIAL", "keyword", "정발")],
        )

        c = SourcingClassifier.from_tables(tables)

        self.assertEqual(c.classify("직구 마우스").category_code, "DIRECT")
        self.assertEqual(c.classify("정발 마우스").status, "none")  # 충돌한 신호는 둘 다 쓰지 않는다
        self.assertEqual(sorted(i.code for i in c.issues), ["SIGNAL_BAD_DOMAIN", "SIGNAL_CONFLICT"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
