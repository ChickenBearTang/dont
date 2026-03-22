from __future__ import annotations


class LLMSummaryPolisher:
    def polish(self, *, decision: str, top_reason_text: str, suggestion_text: str) -> str:
        decision_text = {
            "BUY": "구매 가능",
            "WAIT": "관망 권장",
            "SKIP": "비구매 권장",
        }.get(decision, "추가 검토")
        return f"{decision_text}. 핵심 근거: {top_reason_text} 개선 포인트: {suggestion_text}"
