"""언어 모델 보조 추출 훅과 환각 방어.

규칙 + 카탈로그로 못 푼 제목에 한해 언어 모델에게 '제목에 적힌 제조사와 모델명'을 뽑게 할 수 있다.
하지만 언어 모델은 없는 모델명을 지어내거나 비슷한 다른 모델로 바꿔 쓸 수 있다
(MX Master 3S -> MX Master 4). 그래서 모델이 준 값은 반드시 검증한다:
  - 모델명은 제목에 토큰 경계로 그대로 들어 있어야 한다 (글자 하나라도 다르면 거부)
  - 브랜드는 사전에 있거나 제목에 그대로 있어야 한다
검증을 통과해도 신뢰 상품(RESOLVED_*)으로 올리지 않는다. 카탈로그에 없는 모델이라는
점은 그대로이기 때문이다.

이 저장소는 외부 언어 모델 API 클라이언트를 담지 않는다 (온프레미스 원칙). LlmExtractor 를 구현한 추출기를
ProductResolver(llm=...) 에 넘기면 쓰이고, 안 넘기면 규칙만 쓴다. 온프레미스에서 직접 돌리는 모델을 연결하게
되더라도 verify_llm_candidate 가 같은 방식으로 값을 검증한다.
"""

from __future__ import annotations

from typing import Any, Protocol

from .brands import BrandLexicon
from .text import compact, compact_code, find_on_boundaries, tokenize


class LlmExtractor(Protocol):
    def extract(self, title: str) -> dict[str, Any] | None:
        """{'brand': str|None, 'model': str|None} 를 돌려준다. 모르면 None 값."""
        ...


def verify_llm_candidate(
    title: str, brand: object, model: object, lexicon: BrandLexicon
) -> tuple[bool, str]:
    """(통과 여부, 사유). 통과하면 모델이 제목에 그대로 있고 브랜드가 근거 있다는 뜻이다."""
    if not isinstance(model, str) or compact_code(model) == "":
        return False, "model_missing"
    haystack = compact(tokenize(title))
    if not find_on_boundaries(haystack, compact_code(model)):
        return False, "model_not_in_title"
    if brand in (None, ""):
        return True, "ok_without_brand"
    if not isinstance(brand, str):
        return False, "brand_invalid"
    if brand.strip().lower() in lexicon.brands():
        return True, "ok"
    if find_on_boundaries(haystack, compact_code(brand)):
        return True, "ok"
    return False, "brand_not_in_title"
