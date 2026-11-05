"""LLM 보조 추출과 환각 방어.

규칙 + 카탈로그로 못 푼 제목에 한해 LLM(Gemini 등)에게 '제목에 적힌 제조사와 모델명'을
뽑게 할 수 있다. 하지만 LLM 은 없는 모델명을 지어내거나 비슷한 다른 모델로 바꿔 쓸 수 있다
(MX Master 3S -> MX Master 4). 그래서 LLM 이 준 값은 반드시 검증한다:
  - 모델명은 제목에 토큰 경계로 그대로 들어 있어야 한다 (글자 하나라도 다르면 거부)
  - 브랜드는 사전에 있거나 제목에 그대로 있어야 한다
검증을 통과해도 신뢰 상품(RESOLVED_*)으로 올리지 않는다. 카탈로그에 없는 모델이라는
점은 그대로이기 때문이다.

GeminiExtractor 는 이 환경에서 실제 API 로 호출해 보지 못했다(키/외부망 없음). 요청 구성과
응답 해석은 가짜 HTTP 함수를 끼워 테스트했을 뿐이며, 운영 연결 전에 실제 키로 한 번 확인해야 한다.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Protocol
from urllib.request import Request, urlopen

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


_PROMPT = (
    "다음은 쇼핑 핫딜 게시글 제목이다. 제목에 '글자 그대로 적혀 있는' 제조사(brand)와 모델명(model)만 "
    "JSON 으로 답하라. 제목에 없는 정보를 추측하거나 비슷한 다른 모델명으로 바꾸지 마라. "
    '확실하지 않으면 해당 값을 null 로 하라. 형식: {"brand": string|null, "model": string|null}\n제목: '
)


def _default_post(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - 사용자가 지정한 API 주소
        return json.loads(response.read().decode("utf-8"))


class GeminiExtractor:
    """Gemini REST 로 제목에서 제조사/모델명을 뽑는다. 키는 GEMINI_API_KEY 환경변수."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = "gemini-2.5-flash",
        timeout: float = 10.0,
        post: Callable[[str, dict[str, Any], float], dict[str, Any]] = _default_post,
    ) -> None:
        self._key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._model = model
        self._timeout = timeout
        self._post = post

    def extract(self, title: str) -> dict[str, Any] | None:
        if not self._key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._key}"
        body = {
            "contents": [{"parts": [{"text": _PROMPT + title}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
        }
        try:
            payload = self._post(url, body, self._timeout)
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
        except Exception:  # 네트워크/형식 오류는 '모름'으로 취급한다
            return None
        return data if isinstance(data, dict) else None
