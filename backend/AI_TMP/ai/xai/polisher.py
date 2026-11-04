from __future__ import annotations

_LEAD = {
    "BUY_NOW": "지금 구매해도 좋은 조건입니다.",
    "WAIT": "조금 더 지켜보는 것을 권합니다.",
    "NOT_RECOMMENDED": "지금은 구매를 권하지 않습니다.",
}
_DEFAULT_LEAD = "구매 전에 한 번 더 검토해 보세요."


def _sentence(text: str) -> str:
    text = " ".join(str(text).split())
    if text == "":
        return ""
    return text if text[-1] in ".!?。" else text + "."


class LLMSummaryPolisher:
    """판단, 핵심 근거, 개선 방법을 자연스러운 한 단락으로 잇는다.

    이름과 달리 LLM 을 쓰지 않는 결정적 템플릿이다 (온프레미스에서 그대로 동작,
    같은 입력은 같은 문장). 이전에는 "구매 권장. 핵심 근거: ... 개선 포인트: ..." 처럼
    항목을 이름표로 이어 붙여 읽기 어색했다.
    """

    def polish(
        self, *, decision: str, top_reason_text: str, suggestion_text: str
    ) -> str:
        parts = [
            _LEAD.get(decision, _DEFAULT_LEAD),
            _sentence(top_reason_text),
            _sentence(suggestion_text),
        ]
        return " ".join(part for part in parts if part)
