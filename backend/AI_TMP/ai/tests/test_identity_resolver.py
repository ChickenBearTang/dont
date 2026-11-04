"""제조사·모델 단위 상품 식별 테스트.

핵심 성질: '다른 모델을 같은 상품으로 합치지 않는다' (오병합 0). 못 정하면 고르지 않고
이유와 후보를 돌려준다. 카탈로그는 초기 예시(검수 전)이고, 테스트는 설계 성질을 본다.
"""

from __future__ import annotations

import unittest

from ..crawler.identity import (
    BrandLexicon,
    Catalog,
    IdentityStatus,
    ProductResolver,
    is_valid_gtin,
    normalize_gtin,
)

R = IdentityStatus


def resolver(**kw):
    return ProductResolver(**kw)


def resolve(title, **kw):
    return resolver().resolve(title, **kw)


class VariantDiscriminationTest(unittest.TestCase):
    """한 글자 차이로 다른 상품이 되는 경우."""

    def check(self, title, expected_id):
        identity = resolve(title)
        self.assertEqual(identity.status, R.RESOLVED_CATALOG, (title, identity))
        self.assertEqual(identity.canonical_id, expected_id, title)

    def test_MX_Master_3S와_4와_3은_서로_다르다(self) -> None:
        self.check("로지텍 MX Master 3S 무선 마우스", "logitech:mx-master-3s")
        self.check("로지텍 MX Master 4 무선 마우스", "logitech:mx-master-4")
        self.check("로지텍 MX Master 3 무선 마우스", "logitech:mx-master-3")
        self.check("로지텍 MX Master 2S 무선 마우스", "logitech:mx-master-2s")

    def test_G304와_G305는_서로_다르다(self) -> None:
        self.check("로지텍 G304 무선 게이밍 마우스", "logitech:g304")
        self.check("로지텍 G305 무선 게이밍 마우스", "logitech:g305")

    def test_SUPER와_Ti가_붙으면_다른_그래픽카드다(self) -> None:
        self.check("RTX 4070 그래픽카드", "nvidia:rtx-4070")
        self.check("RTX 4070 SUPER 그래픽카드", "nvidia:rtx-4070-super")
        self.check("RTX 4070 Ti 그래픽카드", "nvidia:rtx-4070-ti")
        self.check("RTX 4070 Ti SUPER 그래픽카드", "nvidia:rtx-4070-ti-super")

    def test_버즈2와_버즈2_프로는_다르다(self) -> None:
        self.check("삼성 갤럭시 버즈2 프로", "samsung:galaxy-buds2-pro")
        self.check("삼성 갤럭시 버즈2", "samsung:galaxy-buds2")

    def test_표기_차이는_같은_상품이다(self) -> None:
        for title in ["로지텍 mx master 3s", "로지텍 MX-Master-3S", "로지텍 MXMaster3S", "Logitech MX Master 3S Mouse",
                      "로지텍 엠엑스 마스터 3S", "로지텍 MX Master 3S무선"]:
            with self.subTest(title=title):
                self.check(title, "logitech:mx-master-3s")

    def test_한글_표기_별칭(self) -> None:
        self.check("애플 에어팟 프로 2 정품", "apple:airpods-pro-2")
        self.check("에어팟4 노이즈캔슬링", "apple:airpods-4")


class UnknownSuffixTest(unittest.TestCase):
    """카탈로그에 없는 변형어가 모델명 뒤에 붙으면 기본형으로 합치지 않는다 (실제로 발견된 오병합)."""

    def test_MX_Keys_Mini는_MX_Keys가_아니다(self) -> None:
        identity = resolve("로지텍 MX Keys Mini 키보드 무선")

        self.assertEqual(identity.status, R.AMBIGUOUS_VARIANT)
        self.assertIsNone(identity.canonical_id)
        self.assertFalse(identity.trusted)
        self.assertIn("logitech:mx-keys", identity.candidates)

    def test_변형어가_다르면_그룹_키도_다르다(self) -> None:
        mini = resolve("로지텍 MX Keys Mini 키보드")
        base = resolve("로지텍 MX Keys 키보드")

        self.assertNotEqual(mini.group_key, base.group_key)
        self.assertTrue(mini.group_key.startswith("unverified:"))
        self.assertEqual(base.group_key, "logitech:mx-keys")

    def test_for_Mac_for_Business_같은_판매_변형도_확정하지_않는다(self) -> None:
        for title in ["로지텍 MX Master 3S for Mac", "로지텍 MX Master 3S for Business"]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).status, R.AMBIGUOUS_VARIANT)

    def test_무해한_꼬리말은_확정을_막지_않는다(self) -> None:
        for title in ["로지텍 MX Master 3S 무선 마우스 정품", "로지텍 MX Master 3S 블랙", "로지텍 MX Master 3S 109,000원",
                      "로지텍 MX Master 3S (무료배송)", "RTX 4070 SUPER 12GB 그래픽카드", "로지텍 G304 라이트스피드"]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).status, R.RESOLVED_CATALOG, title)

    def test_알_수_없는_한글_설명어는_통과한다(self) -> None:
        """설명어는 끝이 없다. 변형어 목록에 없는 한글 꼬리말까지 막으면 거의 아무것도 확정하지 못한다."""
        for title in ["에어팟4 노이즈캔슬링", "로지텍 MX Master 3S 인체공학 마우스", "삼성 갤럭시 버즈2 프로 충전케이스"]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).status, R.RESOLVED_CATALOG, title)

    def test_알려진_변형어는_한글이어도_막는다(self) -> None:
        for title in ["로지텍 MX Keys 미니", "로지텍 MX Keys 플러스"]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).status, R.AMBIGUOUS_VARIANT, title)

    def test_알_수_없는_영문_꼬리말은_막는다(self) -> None:
        for title in ["로지텍 MX Master 3S xl", "로지텍 G304 v2", "로지텍 MX Keys S2"]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).status, R.AMBIGUOUS_VARIANT, title)

    def test_모델명_끝이면_확정한다(self) -> None:
        self.assertEqual(resolve("로지텍 MX Master 3S").status, R.RESOLVED_CATALOG)


class RefusalTest(unittest.TestCase):
    def test_버전을_말하지_않으면_추측하지_않고_후보를_준다(self) -> None:
        identity = resolve("로지텍 MX Master 마우스 특가")

        self.assertEqual(identity.status, R.AMBIGUOUS_VARIANT)
        self.assertIsNone(identity.canonical_id)
        self.assertEqual(
            set(identity.candidates),
            {"logitech:mx-master-3s", "logitech:mx-master-3", "logitech:mx-master-2s", "logitech:mx-master-4"},
        )

    def test_묶음_제목은_하나로_고르지_않는다(self) -> None:
        identity = resolve("에어팟 프로 2 / 에어팟 4 세트")

        self.assertEqual(identity.status, R.MULTIPLE_PRODUCTS)
        self.assertIsNone(identity.canonical_id)

    def test_브랜드와_모델이_충돌하면_맞추지_않는다(self) -> None:
        identity = resolve("삼성 MX Master 3S")

        self.assertEqual(identity.status, R.UNRESOLVED)
        self.assertIsNone(identity.canonical_id)
        self.assertTrue(any("BRAND_MODEL_CONFLICT" in w for w in identity.warnings))

    def test_브랜드가_없어도_모델이_유일하면_카탈로그로_식별하되_확신도가_낮다(self) -> None:
        with_brand = resolve("로지텍 G304")
        without = resolve("G304 무선 마우스")

        self.assertEqual(without.canonical_id, "logitech:g304")
        self.assertLess(without.confidence, with_brand.confidence)

    def test_아무것도_모르면_UNRESOLVED(self) -> None:
        identity = resolve("오늘의 핫딜 모음")

        self.assertEqual(identity.status, R.UNRESOLVED)
        self.assertIsNone(identity.canonical_id)

    def test_브랜드만_있으면_BRAND_ONLY(self) -> None:
        self.assertEqual(resolve("로지텍 마우스 할인").status, R.BRAND_ONLY)

    def test_빈_제목(self) -> None:
        self.assertEqual(resolve("").status, R.UNRESOLVED)
        self.assertEqual(resolve(None).status, R.UNRESOLVED)  # type: ignore[arg-type]


class UnverifiedTest(unittest.TestCase):
    def test_카탈로그에_없는_모델은_추정만_하고_신뢰하지_않는다(self) -> None:
        identity = resolve("로지텍 M590 무선 마우스")

        self.assertEqual(identity.status, R.UNVERIFIED_MODEL)
        self.assertEqual(identity.model, "m590")
        self.assertIsNone(identity.canonical_id)
        self.assertEqual(identity.group_key, "unverified:logitech:m590")
        self.assertFalse(identity.trusted)

    def test_신뢰하는_식별만_canonical_id를_가진다(self) -> None:
        samples = ["로지텍 MX Master 3S", "로지텍 M590", "로지텍 마우스", "삼성 MX Master 3S", "로지텍 MX Master 마우스", "x"]
        for title in samples:
            identity = resolve(title)
            self.assertEqual(identity.canonical_id is not None, identity.trusted, (title, identity.status))


class GtinTest(unittest.TestCase):
    def test_체크_숫자가_맞는_바코드만_유효하다(self) -> None:
        for valid in ["4006381333931", "036000291452", "96385074", "00012345678905"]:
            self.assertTrue(is_valid_gtin(valid), valid)
        for invalid in ["4006381333932", "123", "abcdefghijklm", "0000000000000", "", None, 4006381333931]:
            self.assertFalse(is_valid_gtin(invalid), invalid)

    def test_정규화는_14자리로_맞춘다(self) -> None:
        self.assertEqual(normalize_gtin("4006381333931"), "04006381333931")
        self.assertEqual(normalize_gtin("4006-3813-33931"), "04006381333931")
        self.assertIsNone(normalize_gtin("4006381333932"))

    def test_제목의_바코드로_식별한다(self) -> None:
        identity = resolve("[직구] 어떤 상품 EAN 4006381333931")

        self.assertEqual(identity.status, R.RESOLVED_GTIN)
        self.assertEqual(identity.canonical_id, "gtin:04006381333931")

    def test_가격이나_전화번호처럼_보이는_숫자는_바코드가_아니다(self) -> None:
        for title in ["로지텍 마우스 12345678901 문의", "가격 1234567890123원"]:
            self.assertNotEqual(resolve(title).status, R.RESOLVED_GTIN, title)


class LexiconTest(unittest.TestCase):
    def test_짧은_별칭이_다른_브랜드_안에서_잡히지_않는다(self) -> None:
        lex = BrandLexicon.load()

        self.assertEqual(lex.detect("MSI 노트북"), ["msi"])  # 'ms'(마이크로소프트)로 잡히면 안 된다
        self.assertEqual(lex.detect("LG 그램"), ["lg"])
        self.assertNotIn("lg", lex.detect("로지텍 마우스"))

    def test_한글_영문_별칭이_같은_브랜드다(self) -> None:
        lex = BrandLexicon.load()

        self.assertEqual(lex.detect("로지텍"), lex.detect("Logitech"))

    def test_별칭이_두_브랜드에_걸리면_거부한다(self) -> None:
        with self.assertRaises(ValueError):
            BrandLexicon({"a": ["x"], "b": ["x"]})


class CatalogTest(unittest.TestCase):
    def test_시드_카탈로그가_읽히고_모두_미검수다(self) -> None:
        catalog = Catalog.load()

        self.assertGreater(len(catalog), 30)
        self.assertTrue(all(not e.verified for e in catalog._entries))

    def test_같은_표기를_두_상품이_주장하면_거부한다(self) -> None:
        from ..crawler.identity.catalog import CatalogEntry

        a = CatalogEntry("a", "x", "L", "Model 1", "c", aliases=("alias",))
        b = CatalogEntry("b", "x", "L", "Model 2", "c", aliases=("alias",))

        with self.assertRaises(ValueError):
            Catalog([a, b])

    def test_카탈로그_ID_중복을_거부한다(self) -> None:
        from ..crawler.identity.catalog import CatalogEntry

        a = CatalogEntry("a", "x", "L", "Model 1", "c")
        with self.assertRaises(ValueError):
            Catalog([a, CatalogEntry("a", "x", "L", "Model 2", "c")])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class AccessoryTest(unittest.TestCase):
    """액세서리 글은 본체가 아니다. 케이스 가격이 본체 가격 이력에 섞이면 안 된다."""

    def test_케이스_커버_필름_등은_본체로_확정하지_않는다(self) -> None:
        for title in ["삼성 갤럭시 버즈2 프로 케이스", "에어팟 프로 2 실리콘 케이스", "로지텍 MX Master 3S 전용 파우치",
                      "갤럭시 버즈2 프로 호환 이어팁", "로지텍 G304 마우스 스티커"]:
            with self.subTest(title=title):
                identity = resolve(title)
                self.assertEqual(identity.status, R.ACCESSORY_SUSPECTED, title)
                self.assertIsNone(identity.canonical_id)

    def test_충전케이스처럼_본체의_일부를_말하는_단어는_액세서리가_아니다(self) -> None:
        self.assertEqual(resolve("삼성 갤럭시 버즈2 프로 충전케이스 포함").status, R.RESOLVED_CATALOG)

    def test_액세서리_판정이_후보_본체를_알려준다(self) -> None:
        identity = resolve("삼성 갤럭시 버즈2 프로 케이스")

        self.assertIn("samsung:galaxy-buds2-pro", identity.candidates)


class PartNumberTest(unittest.TestCase):
    def test_제조사_모델_코드가_뒤에_붙어도_확정한다(self) -> None:
        for title, expected in [
            ("삼성전자 갤럭시 버즈2 프로 SM-R510 (129,000원)", "samsung:galaxy-buds2-pro"),
            ("로지텍 MX Master 3S 910-006556 무선 마우스", "logitech:mx-master-3s"),
        ]:
            with self.subTest(title=title):
                identity = resolve(title)
                self.assertEqual(identity.status, R.RESOLVED_CATALOG, title)
                self.assertEqual(identity.canonical_id, expected)

    def test_부품번호_뒤에_변형어가_오면_여전히_확정하지_않는다(self) -> None:
        self.assertEqual(resolve("로지텍 MX Keys 920-009 mini").status, R.AMBIGUOUS_VARIANT)


class CompatibleBrandTest(unittest.TestCase):
    def test_그래픽카드는_제조_파트너_브랜드가_제목에_있어도_식별한다(self) -> None:
        for title in ["MSI RTX 4070 SUPER 12GB 벤투스 (689,000원)", "ASUS RTX 4070 Ti SUPER 듀얼", "기가바이트 RTX 4060 Ti 윈드포스"]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).status, R.RESOLVED_CATALOG, title)
        self.assertEqual(resolve("MSI RTX 4070 SUPER 12GB").canonical_id, "nvidia:rtx-4070-super")

    def test_그래픽카드가_아닌_상품은_파트너_브랜드로_맞추지_않는다(self) -> None:
        self.assertEqual(resolve("MSI MX Master 3S").status, R.UNRESOLVED)


class EvaluationFindingsTest(unittest.TestCase):
    """평가 세트가 드러낸 문제를 고정한다."""

    def test_교체용_이어패드는_소모품이다(self) -> None:
        for title in ["소니 WH-1000XM5 이어패드 교체용", "소니 WH-1000XM5 이어패드"]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).status, R.ACCESSORY_SUSPECTED, title)

    def test_신제품은_마케팅_문구이지_변형어가_아니다(self) -> None:
        self.assertEqual(resolve("로지텍 엠엑스 마스터 4 신제품 무료배송").canonical_id, "logitech:mx-master-4")

    def test_USB_C_Type_C_MagSafe_같은_연결_규격은_변형이_아니다(self) -> None:
        for title in ["애플 에어팟 프로 2 (USB-C) 정품", "에어팟 프로 2 Type-C 정품", "에어팟 프로 2 MagSafe 정품", "에어팟 프로 2 Lightning"]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).canonical_id, "apple:airpods-pro-2", title)

    def test_충전케이스_포함은_액세서리가_아니다(self) -> None:
        for title in ["에어팟프로2 MagSafe 충전 케이스 포함 정품", "애플 에어팟 3 MagSafe 충전 케이스 (139,000원)", "에어팟 프로 2 케이스 포함"]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).status, R.RESOLVED_CATALOG, title)

    def test_케이스만_따로_파는_글은_여전히_액세서리다(self) -> None:
        self.assertEqual(resolve("에어팟 프로 2 케이스 커버").status, R.ACCESSORY_SUSPECTED)

    def test_그래픽카드_파트너_제품명은_변형이_아니다(self) -> None:
        for title, expected in [
            ("ASUS RTX 4080 SUPER 16GB TUF 그래픽카드", "nvidia:rtx-4080-super"),
            ("MSI RTX 4070TI SUPER 벤투스 3X", "nvidia:rtx-4070-ti-super"),
            ("ASUS 지포스 RTX 4070 SUPER DUAL OC 12GB", "nvidia:rtx-4070-super"),
            ("기가바이트 RTX 4060 윈드포스 OC 8GB", "nvidia:rtx-4060"),
        ]:
            with self.subTest(title=title):
                self.assertEqual(resolve(title).canonical_id, expected, title)

    def test_그래픽카드의_진짜_변형은_여전히_막는다(self) -> None:
        """TUF/OC 는 허용해도 Ti/SUPER 같은 칩 변형이 카탈로그에 없는 조합이면 확정하지 않는다."""
        self.assertNotEqual(resolve("ASUS RTX 4060 Ti SUPER TUF").status, R.RESOLVED_CATALOG)

    def test_다른_상품의_꼬리말은_그래픽카드_허용어가_적용되지_않는다(self) -> None:
        self.assertEqual(resolve("로지텍 MX Master 3S TUF").status, R.AMBIGUOUS_VARIANT)


class CanonicalIdGuardTest(unittest.TestCase):
    """호출부가 실수로 id 를 넘겨도 신뢰하지 못하는 식별에는 canonical_id 가 붙지 않는다."""

    def test_신뢰하지_않는_상태에는_id를_붙이지_않는다(self) -> None:
        for status in (R.AMBIGUOUS_VARIANT, R.ACCESSORY_SUSPECTED, R.MULTIPLE_PRODUCTS, R.UNVERIFIED_MODEL, R.BRAND_ONLY, R.UNRESOLVED):
            with self.subTest(status=status):
                identity = ProductResolver._make(status, "logitech:g304", "logitech", "G304", 0.9, "test", (), (), (), "t")

                self.assertIsNone(identity.canonical_id)
                self.assertTrue(identity.group_key.startswith("unverified:"))
                self.assertFalse(identity.trusted)

    def test_신뢰하는_상태에는_id가_붙는다(self) -> None:
        for status in (R.RESOLVED_GTIN, R.RESOLVED_MPN, R.RESOLVED_CATALOG):
            with self.subTest(status=status):
                identity = ProductResolver._make(status, "x:1", "b", "m", 0.9, "test", (), (), (), "t")

                self.assertEqual(identity.canonical_id, "x:1")
                self.assertEqual(identity.group_key, "x:1")
                self.assertTrue(identity.trusted)
